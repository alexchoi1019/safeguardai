package com.example.safeguardai

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import androidx.core.app.NotificationCompat
import okhttp3.MediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.io.File

class DetectionService : Service() {

    companion object {
        private const val CHANNEL_ID = "SafeguardAI_Channel"
        private const val NOTIFICATION_ID = 1
        private const val RECORDING_DURATION_MS = 5000L
        
        const val ACTION_DETECTION_RESULT = "com.example.safeguardai.ACTION_DETECTION_RESULT"
        const val EXTRA_RESULT = "extra_result"
        const val EXTRA_ERROR = "extra_error"
    }

    private lateinit var audioRecorder: AudioRecorder
    private val serviceHandler = Handler(Looper.getMainLooper())
    
    private var isRecording = false
    private var isRequesting = false
    private var isServiceRunning = false

    override fun onCreate() {
        super.onCreate()
        audioRecorder = AudioRecorder(this)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (!isServiceRunning) {
            isServiceRunning = true
            createNotificationChannel()
            startForeground(NOTIFICATION_ID, createNotification())
            startDetectionLoop()
        }
        return START_STICKY
    }

    private fun startDetectionLoop() {
        if (!isServiceRunning || isRecording || isRequesting) return

        val recordedFile = audioRecorder.startRecording()
        if (recordedFile == null) {
            broadcastError("녹음을 시작하지 못했습니다.")
            stopSelf()
            return
        }

        isRecording = true
        serviceHandler.postDelayed({
            finishCurrentRecording()
        }, RECORDING_DURATION_MS)
    }

    private fun finishCurrentRecording() {
        if (!isRecording) return

        val file = audioRecorder.stopRecording()
        isRecording = false

        if (!isServiceRunning) {
            file?.delete()
            return
        }

        if (file != null && file.exists() && file.length() > 0L) {
            sendAudioToServer(file)
        } else {
            serviceHandler.postDelayed({
                startDetectionLoop()
            }, 500L)
        }
    }

    private fun sendAudioToServer(file: File) {
        if (!isServiceRunning || isRequesting) {
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
                    val result = response.body()
                    result?.let {
                        broadcastResult(it)
                    }
                } else {
                    broadcastError("서버 응답 오류: ${response.code()}")
                }

                if (isServiceRunning) {
                    startDetectionLoop()
                }
            }

            override fun onFailure(call: Call<AnalyzeResponse>, t: Throwable) {
                isRequesting = false
                file.delete()
                broadcastError("서버 연결 실패")

                if (isServiceRunning) {
                    serviceHandler.postDelayed({
                        startDetectionLoop()
                    }, 2000L)
                }
            }
        })
    }

    private fun broadcastResult(result: AnalyzeResponse) {
        val intent = Intent(ACTION_DETECTION_RESULT)
        intent.putExtra(EXTRA_RESULT, result)
        sendBroadcast(intent)
    }

    private fun broadcastError(message: String) {
        val intent = Intent(ACTION_DETECTION_RESULT)
        intent.putExtra(EXTRA_ERROR, message)
        sendBroadcast(intent)
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                CHANNEL_ID,
                getString(R.string.notification_channel_name),
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(serviceChannel)
        }
    }

    private fun createNotification(): Notification {
        val notificationIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, notificationIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.notification_title))
            .setContentText(getString(R.string.notification_content))
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentIntent(pendingIntent)
            .build()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        isServiceRunning = false
        serviceHandler.removeCallbacksAndMessages(null)
        if (isRecording) {
            audioRecorder.stopRecording()?.delete()
        }
        super.onDestroy()
    }
}
