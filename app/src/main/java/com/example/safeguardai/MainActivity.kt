package com.example.safeguardai

import android.Manifest
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.widget.Button
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.constraintlayout.widget.ConstraintLayout
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

enum class RiskLevel {
    SAFE,
    WARNING,
    DANGER
}

class MainActivity : AppCompatActivity() {

    companion object {
        private const val PERMISSION_REQUEST_CODE = 1000
        private const val MAX_RISK_HISTORY = 3
    }

    private lateinit var rootLayout: ConstraintLayout
    private lateinit var scrollView: ScrollView
    private lateinit var tvStatus: TextView
    private lateinit var tvRiskScore: TextView
    private lateinit var tvRiskLevelBadge: TextView
    private lateinit var pbRisk: ProgressBar
    private lateinit var tvReasons: TextView
    private lateinit var tvActions: TextView
    private lateinit var btnReport: Button
    private lateinit var btnStart: Button

    private var isDetecting = false

    private val recentRiskFactors = ArrayDeque<List<RiskFactor>>()
    private val accumulatedReasons = linkedSetOf<String>()
    private val accumulatedActions = linkedSetOf<String>()
    private var previousRiskLevel = RiskLevel.SAFE

    private val detectionReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == DetectionService.ACTION_DETECTION_RESULT) {
                val result = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    intent.getSerializableExtra(DetectionService.EXTRA_RESULT, AnalyzeResponse::class.java)
                } else {
                    @Suppress("DEPRECATION")
                    intent.getSerializableExtra(DetectionService.EXTRA_RESULT) as? AnalyzeResponse
                }

                val error = intent.getStringExtra(DetectionService.EXTRA_ERROR)

                if (result != null) {
                    tvStatus.text = getString(R.string.status_analyzing)
                    updateRiskUi(result)
                } else if (error != null) {
                    tvStatus.text = error
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        rootLayout = findViewById(R.id.rootLayout)
        scrollView = findViewById(R.id.scrollView)
        tvStatus = findViewById(R.id.tvStatus)
        tvRiskScore = findViewById(R.id.tvRiskScore)
        tvRiskLevelBadge = findViewById(R.id.tvRiskLevelBadge)
        pbRisk = findViewById(R.id.pbRisk)
        tvReasons = findViewById(R.id.tvReasons)
        tvActions = findViewById(R.id.tvActions)
        btnReport = findViewById(R.id.btnReport)
        btnStart = findViewById(R.id.btnStart)

        btnStart.setOnClickListener {
            if (isDetecting) {
                stopDetection()
            } else {
                checkPermissions()
            }
        }

        btnReport.setOnClickListener {
            val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:112"))
            startActivity(intent)
        }
    }

    override fun onResume() {
        super.onResume()
        val filter = IntentFilter(DetectionService.ACTION_DETECTION_RESULT)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(detectionReceiver, filter, RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(detectionReceiver, filter)
        }
    }

    override fun onPause() {
        super.onPause()
        unregisterReceiver(detectionReceiver)
    }

    private fun checkPermissions() {
        val permissions = mutableListOf(Manifest.permission.RECORD_AUDIO)
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            permissions.add(Manifest.permission.FOREGROUND_SERVICE_MICROPHONE)
        }

        val neededPermissions = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (neededPermissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(
                this,
                neededPermissions.toTypedArray(),
                PERMISSION_REQUEST_CODE
            )
        } else {
            startDetection()
        }
    }

    private fun startDetection() {
        if (isDetecting) return

        recentRiskFactors.clear()
        accumulatedReasons.clear()
        accumulatedActions.clear()
        previousRiskLevel = RiskLevel.SAFE

        isDetecting = true
        btnStart.text = getString(R.string.btn_stop_test)
        btnStart.setBackgroundColor(Color.parseColor("#888888"))
        tvStatus.text = getString(R.string.status_safe_normal)
        rootLayout.setBackgroundColor(Color.parseColor("#FFF8F9"))

        val serviceIntent = Intent(this, DetectionService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
    }

    private fun stopDetection() {
        isDetecting = false
        btnStart.text = getString(R.string.btn_start_test)
        btnStart.setBackgroundColor(Color.parseColor("#FF4081"))
        tvStatus.text = getString(R.string.status_waiting)

        val serviceIntent = Intent(this, DetectionService::class.java)
        stopService(serviceIntent)

        Toast.makeText(this, "탐지를 중지했습니다.", Toast.LENGTH_SHORT).show()
    }

    private fun updateRiskUi(result: AnalyzeResponse) {
        val instantScore = result.riskScore
        val cumulativeScore = calculateCumulativeRisk(result.riskFactors)
        val score = maxOf(instantScore, cumulativeScore)
        val currentRiskLevel = getRiskLevel(score)

        tvRiskScore.text = getString(R.string.risk_score_format, score.toInt())
        pbRisk.progress = score.toInt()

        for (reason in result.reasons) {
            if (reason !in accumulatedReasons) {
                if (accumulatedReasons.size >= 5) {
                    accumulatedReasons.remove(accumulatedReasons.first())
                }
                accumulatedReasons.add(reason)
            }
        }
        
        if (accumulatedReasons.isNotEmpty()) {
            tvReasons.text = accumulatedReasons.joinToString(separator = "\n") { "• $it" }
        } else {
            tvReasons.text = getString(R.string.reason_empty)
        }

        for (action in result.actions) {
            if (action !in accumulatedActions) {
                if (accumulatedActions.size >= 5) {
                    accumulatedActions.remove(accumulatedActions.first())
                }
                accumulatedActions.add(action)
            }
        }
        
        if (accumulatedActions.isNotEmpty()) {
            tvActions.text = accumulatedActions.joinToString(separator = "\n") { "• $it" }
        } else {
            tvActions.text = getString(R.string.action_empty)
        }
        
        scrollView.post {
            scrollView.fullScroll(ScrollView.FOCUS_DOWN)
        }

        when (currentRiskLevel) {
            RiskLevel.DANGER -> {
                rootLayout.setBackgroundColor(Color.parseColor("#FFF0F3"))
                tvRiskLevelBadge.text = getString(R.string.level_danger)
                tvRiskLevelBadge.setBackgroundResource(R.drawable.bg_badge_danger)
                tvStatus.text = getString(R.string.status_phishing_heavy)
                tvStatus.setTextColor(Color.parseColor("#D81B60"))
                tvRiskScore.setTextColor(Color.parseColor("#D81B60"))

                if (previousRiskLevel != RiskLevel.DANGER) {
                    triggerVibration()
                    showWarningDialog(result.text)
                }
            }
            RiskLevel.WARNING -> {
                rootLayout.setBackgroundColor(Color.parseColor("#FFF9F0"))
                tvRiskLevelBadge.text = getString(R.string.level_warning)
                tvRiskLevelBadge.setBackgroundResource(R.drawable.bg_badge_warning)
                tvStatus.text = getString(R.string.status_suspicious_word)
                tvStatus.setTextColor(Color.parseColor("#E65100"))
                tvRiskScore.setTextColor(Color.parseColor("#E65100"))
            }
            RiskLevel.SAFE -> {
                rootLayout.setBackgroundColor(Color.parseColor("#F1F8F1"))
                tvRiskLevelBadge.text = getString(R.string.level_safe)
                tvRiskLevelBadge.setBackgroundResource(R.drawable.bg_badge_safe)
                tvStatus.text = getString(R.string.status_safe_normal)
                tvStatus.setTextColor(Color.parseColor("#2E7D32"))
                tvRiskScore.setTextColor(Color.parseColor("#2E7D32"))
            }
        }
        previousRiskLevel = currentRiskLevel
    }

    private fun calculateCumulativeRisk(newFactors: List<RiskFactor>): Float {
        recentRiskFactors.addLast(newFactors)
        if (recentRiskFactors.size > MAX_RISK_HISTORY) {
            recentRiskFactors.removeFirst()
        }

        val uniqueFactors = mutableMapOf<String, Float>()
        for (factorList in recentRiskFactors) {
            for (factor in factorList) {
                uniqueFactors[factor.category] = maxOf(uniqueFactors[factor.category] ?: 0f, factor.score)
            }
        }
        return uniqueFactors.values.sum().coerceAtMost(100f)
    }

    private fun getRiskLevel(score: Float): RiskLevel {
        return when {
            score >= 70 -> RiskLevel.DANGER
            score >= 35 -> RiskLevel.WARNING
            else -> RiskLevel.SAFE
        }
    }

    private fun triggerVibration() {
        val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
            vibratorManager.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createOneShot(1000, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(1000)
        }
    }

    private fun showWarningDialog(recognizedText: String) {
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.dialog_warning_title))
            .setMessage(getString(R.string.dialog_warning_message, recognizedText))
            .setPositiveButton(getString(R.string.dialog_ok), null)
            .show()
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            if (grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
                startDetection()
            } else {
                Toast.makeText(this, getString(R.string.toast_permission_denied), Toast.LENGTH_SHORT).show()
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
    }
}
