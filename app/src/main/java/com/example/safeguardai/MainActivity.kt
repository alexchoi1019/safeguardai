package com.example.safeguardai

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
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

class MainActivity : AppCompatActivity() {

    companion object {
        private const val RECORD_AUDIO_PERMISSION_CODE = 1000
    }

    private lateinit var tvStatus: TextView
    private lateinit var tvRiskScore: TextView
    private lateinit var btnStart: Button

    private lateinit var audioRecorder: AudioRecorder
    private var isRecording = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        tvStatus = findViewById(R.id.tvStatus)
        tvRiskScore = findViewById(R.id.tvRiskScore)
        btnStart = findViewById(R.id.btnStart)

        audioRecorder = AudioRecorder(this)

        btnStart.setOnClickListener {
            checkAudioPermission()
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
            startTestRecording()
        }
    }

    private fun startTestRecording() {
        if (isRecording) return

        val recordedFile = audioRecorder.startRecording()
        if (recordedFile != null) {
            isRecording = true
            tvStatus.text = getString(R.string.status_collecting)
            tvStatus.setTextColor(Color.parseColor("#333333"))
            Toast.makeText(this, getString(R.string.toast_start_record), Toast.LENGTH_SHORT).show()

            Handler(Looper.getMainLooper()).postDelayed({
                val file = audioRecorder.stopRecording()
                isRecording = false
                
                if (file != null && file.exists()) {
                    tvStatus.text = getString(R.string.status_analyzing)
                    sendAudioToServer(file)
                } else {
                    tvStatus.text = getString(R.string.status_error_record)
                }
            }, 5000)
        }
    }

    // 서버로 오디오 파일 전송 함수
    private fun sendAudioToServer(file: File) {
        val requestFile = RequestBody.create(MediaType.parse("audio/m4a"), file)
        val body = MultipartBody.Part.createFormData("file", file.name, requestFile)

        RetrofitClient.instance.analyzeAudio(body).enqueue(object : Callback<AnalyzeResponse> {
            override fun onResponse(call: Call<AnalyzeResponse>, response: Response<AnalyzeResponse>) {
                if (response.isSuccessful) {
                    val result = response.body()
                    result?.let {
                        val score = it.riskScore
                        tvRiskScore.text = getString(R.string.risk_score_format, score.toInt())

                        // 위험도 점수에 따른 화면 색상 연출
                        if (it.isPhishing || score >= 80) {
                            tvStatus.text = getString(R.string.status_phishing)
                            tvStatus.setTextColor(Color.RED)
                            tvRiskScore.setTextColor(Color.RED)
                        } else if (score >= 40) {
                            tvStatus.text = getString(R.string.status_suspicious)
                            tvStatus.setTextColor(Color.parseColor("#FF9800"))
                            tvRiskScore.setTextColor(Color.parseColor("#FF9800"))
                        } else {
                            tvStatus.text = getString(R.string.status_safe)
                            tvStatus.setTextColor(Color.parseColor("#4CAF50"))
                            tvRiskScore.setTextColor(Color.parseColor("#4CAF50"))
                        }
                    }
                } else {
                    tvStatus.text = getString(R.string.status_server_error, response.code())
                }
            }

            override fun onFailure(call: Call<AnalyzeResponse>, t: Throwable) {
                tvStatus.text = getString(R.string.status_connection_fail)
                Toast.makeText(this@MainActivity, "오류: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == RECORD_AUDIO_PERMISSION_CODE) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startTestRecording()
            } else {
                Toast.makeText(this, getString(R.string.toast_permission_denied), Toast.LENGTH_SHORT).show()
            }
        }
    }
}