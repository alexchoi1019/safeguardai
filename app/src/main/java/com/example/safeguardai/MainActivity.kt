package com.example.safeguardai

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

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

    // 테스트용: 5초간 녹음 후 저장된 파일 확인
    private fun startTestRecording() {
        if (isRecording) return

        val recordedFile = audioRecorder.startRecording()
        if (recordedFile != null) {
            isRecording = true
            tvStatus.text = "🎙️ 5초간 녹음 중입니다..."
            Toast.makeText(this, "녹음 시작!", Toast.LENGTH_SHORT).show()

            // 5초(5000ms) 후에 녹음 자동으로 멈추기
            Handler(Looper.getMainLooper()).postDelayed({
                val file = audioRecorder.stopRecording()
                isRecording = false
                tvStatus.text = "✅ 녹음 완료!"
                
                if (file != null && file.exists()) {
                    Toast.makeText(this, "파일 저장 성공: ${file.name} (${file.length()} bytes)", Toast.LENGTH_LONG).show()
                } else {
                    Toast.makeText(this, "녹음 파일 저장 실패", Toast.LENGTH_SHORT).show()
                }
            }, 5000)
        } else {
            Toast.makeText(this, "녹음을 시작할 수 없습니다.", Toast.LENGTH_SHORT).show()
        }
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