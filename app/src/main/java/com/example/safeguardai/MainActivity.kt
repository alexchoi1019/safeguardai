package com.example.safeguardai

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.widget.Button
import android.widget.ScrollView
import androidx.constraintlayout.widget.ConstraintLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import okhttp3.MediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.io.File

enum class RiskLevel {
    SAFE,
    WARNING,
    DANGER
}

class MainActivity : AppCompatActivity() {

    companion object {
        private const val RECORD_AUDIO_PERMISSION_CODE = 1000
        private const val RECORDING_DURATION_MS = 5000L
        private const val MAX_RISK_HISTORY = 3
    }

    private lateinit var rootLayout: ConstraintLayout
    private lateinit var scrollView: ScrollView
    private lateinit var tvStatus: TextView
    private lateinit var tvRiskScore: TextView
    private lateinit var tvReasons: TextView
    private lateinit var tvActions: TextView
    private lateinit var btnStart: Button

    private lateinit var audioRecorder: AudioRecorder
    private val recordingHandler = Handler(Looper.getMainLooper())

    private var isDetecting = false
    private var isRecording = false
    private var isRequesting = false
    private var continuousErrorCount = 0

    private var currentAudioFile: File? = null

    private val recentRiskFactors = ArrayDeque<List<RiskFactor>>()
    private val accumulatedReasons = linkedSetOf<String>()
    private val accumulatedActions = linkedSetOf<String>()
    private var previousRiskLevel = RiskLevel.SAFE

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        rootLayout = findViewById(R.id.rootLayout)
        scrollView = findViewById(R.id.scrollView)
        tvStatus = findViewById(R.id.tvStatus)
        tvRiskScore = findViewById(R.id.tvRiskScore)
        tvReasons = findViewById(R.id.tvReasons)
        tvActions = findViewById(R.id.tvActions)
        btnStart = findViewById(R.id.btnStart)

        audioRecorder = AudioRecorder(this)

        btnStart.setOnClickListener {
            if (isDetecting) {
                stopDetection()
            } else {
                checkAudioPermission()
            }
        }
    }

    private fun checkAudioPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED) {

            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.RECORD_AUDIO),
                RECORD_AUDIO_PERMISSION_CODE
            )
        } else {
            startDetection()
        }
    }

    private fun startDetection() {
        if (isDetecting) return

        // 상태 초기화
        recentRiskFactors.clear()
        accumulatedReasons.clear()
        accumulatedActions.clear()
        previousRiskLevel = RiskLevel.SAFE
        continuousErrorCount = 0

        isDetecting = true
        btnStart.text = "탐지 중지"

        tvStatus.text = "실시간 탐지를 시작합니다."
        rootLayout.setBackgroundColor(Color.parseColor("#F5F5F5"))
        tvStatus.setTextColor(Color.parseColor("#333333"))

        startNextRecording()
    }

    private fun startNextRecording() {
        if (!isDetecting || isRecording || isRequesting) {
            return
        }

        val recordedFile = audioRecorder.startRecording()

        if (recordedFile == null) {
            tvStatus.text = "녹음을 시작하지 못했습니다."
            stopDetection()
            return
        }

        currentAudioFile = recordedFile
        isRecording = true

        tvStatus.text = "통화 내용을 수집하고 있습니다..."

        recordingHandler.postDelayed({
            finishCurrentRecording()
        }, RECORDING_DURATION_MS)
    }

    private fun finishCurrentRecording() {
        if (!isRecording) {
            return
        }

        val file = audioRecorder.stopRecording()
        isRecording = false
        currentAudioFile = null

        if (!isDetecting) {
            file?.delete()
            return
        }

        if (file != null && file.exists() && file.length() > 0L) {
            tvStatus.text = "음성을 분석하고 있습니다..."
            sendAudioToServer(file)
        } else {
            tvStatus.text = "녹음 파일 생성에 실패했습니다."

            recordingHandler.postDelayed({
                startNextRecording()
            }, 500L)
        }
    }

    private fun stopDetection() {
        isDetecting = false

        recordingHandler.removeCallbacksAndMessages(null)

        if (isRecording) {
            val file = audioRecorder.stopRecording()
            isRecording = false
            file?.delete()
        }

        currentAudioFile = null

        btnStart.text = "탐지 시작"
        tvStatus.text = "탐지가 중지되었습니다."

        Toast.makeText(
            this,
            "실시간 탐지를 중지했습니다.",
            Toast.LENGTH_SHORT
        ).show()
    }

    private fun sendAudioToServer(file: File) {
        if (!isDetecting || isRequesting) {
            file.delete()
            return
        }

        isRequesting = true

        val requestFile = RequestBody.create(MediaType.parse("audio/m4a"), file)
        val body = MultipartBody.Part.createFormData("file", file.name, requestFile)

        RetrofitClient.instance.analyzeAudio(body).enqueue(object : Callback<AnalyzeResponse> {
            override fun onResponse(call: Call<AnalyzeResponse>, response: Response<AnalyzeResponse>) {
                isRequesting = false
                file.delete()

                if (response.isSuccessful) {
                    continuousErrorCount = 0
                    val result = response.body()
                    result?.let {
                        updateRiskUi(it)
                    }
                } else {
                    continuousErrorCount++
                    tvStatus.text = getString(R.string.status_server_error, response.code())
                }

                if (isDetecting) {
                    // 에러가 반복되면 재시도 간격을 조금 늘림
                    val delay = if (continuousErrorCount > 0) 2000L else 0L
                    recordingHandler.postDelayed({
                        startNextRecording()
                    }, delay)
                }
            }

            override fun onFailure(call: Call<AnalyzeResponse>, t: Throwable) {
                isRequesting = false
                file.delete()
                continuousErrorCount++

                tvStatus.text = getString(R.string.status_connection_fail)
                
                // 3번 연속 실패 시 토스트로 경고 (사용자 경험 개선)
                if (continuousErrorCount == 3) {
                    Toast.makeText(this@MainActivity, "서버 연결이 불안정합니다. IP와 Wi-Fi를 확인해주세요.", Toast.LENGTH_LONG).show()
                }

                if (isDetecting) {
                    // 실패 시 2초 뒤 재시도
                    recordingHandler.postDelayed({
                        startNextRecording()
                    }, 2000L)
                }
            }
        })
    }

    private fun updateRiskUi(result: AnalyzeResponse) {
        val instantScore = result.riskScore
        val cumulativeScore = calculateCumulativeRisk(result.riskFactors)
        
        // 실시간 점수와 누적 점수 중 더 높은 것을 사용
        val score = maxOf(instantScore, cumulativeScore)
        val currentRiskLevel = getRiskLevel(score)

        tvRiskScore.text = getString(R.string.risk_score_format, score.toInt())

        // 탐지 근거 누적 및 표시 (최근 5개 유지)
        for (reason in result.reasons) {
            if (reason !in accumulatedReasons) {
                if (accumulatedReasons.size >= 5) {
                    val first = accumulatedReasons.first()
                    accumulatedReasons.remove(first)
                }
                accumulatedReasons.add(reason)
            }
        }
        
        if (accumulatedReasons.isNotEmpty()) {
            val reasonText = accumulatedReasons.joinToString(separator = "\n") { "• $it" }
            tvReasons.text = reasonText
        } else {
            tvReasons.text = getString(R.string.reason_empty)
        }

        // 행동 지침 누적 및 표시 (최근 5개 유지)
        for (action in result.actions) {
            if (action !in accumulatedActions) {
                if (accumulatedActions.size >= 5) {
                    val first = accumulatedActions.first()
                    accumulatedActions.remove(first)
                }
                accumulatedActions.add(action)
            }
        }
        
        if (accumulatedActions.isNotEmpty()) {
            val actionText = accumulatedActions.joinToString(separator = "\n") { "• $it" }
            tvActions.text = actionText
        } else {
            tvActions.text = getString(R.string.action_empty)
        }
        
        // 데이터 업데이트 후 하단으로 스크롤
        scrollView.post {
            scrollView.fullScroll(ScrollView.FOCUS_DOWN)
        }

        // 3단계 위험도별 화면 연출
        when (currentRiskLevel) {
            RiskLevel.DANGER -> {
                // 70점 이상: 위험 (빨간 배경 + 진동 + 경고 팝업)
                rootLayout.setBackgroundColor(Color.parseColor("#FFEBEE"))
                tvStatus.text = getString(R.string.status_phishing_heavy)
                tvStatus.setTextColor(Color.RED)
                tvRiskScore.setTextColor(Color.RED)

                // 최초 DANGER 진입 시에만 알림 발생 (피드백 안정화)
                if (previousRiskLevel != RiskLevel.DANGER) {
                    triggerVibration()
                    showWarningDialog(result.text)
                }
            }
            RiskLevel.WARNING -> {
                // 35~69점: 주의 (주황 배경)
                rootLayout.setBackgroundColor(Color.parseColor("#FFF3E0"))
                tvStatus.text = getString(R.string.status_suspicious_word)
                tvStatus.setTextColor(Color.parseColor("#E65100"))
                tvRiskScore.setTextColor(Color.parseColor("#E65100"))
            }
            RiskLevel.SAFE -> {
                // 0~34점: 안전 (초록 배경)
                rootLayout.setBackgroundColor(Color.parseColor("#E8F5E9"))
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
                // 각 카테고리별 최대 점수를 유지하여 중복 합산 방지
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

    // 진동 울리기 함수
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

    // 경고 팝업 창
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
        if (requestCode == RECORD_AUDIO_PERMISSION_CODE) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startDetection()
            } else {
                Toast.makeText(this, getString(R.string.toast_permission_denied), Toast.LENGTH_SHORT).show()
            }
        }
    }

    override fun onDestroy() {
        isDetecting = false

        recordingHandler.removeCallbacksAndMessages(null)

        if (isRecording) {
            audioRecorder.stopRecording()?.delete()
            isRecording = false
        }

        currentAudioFile?.delete()
        currentAudioFile = null

        super.onDestroy()
    }
}