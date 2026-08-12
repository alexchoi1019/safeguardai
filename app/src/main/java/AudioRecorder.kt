package com.example.safeguardai

import android.content.Context
import android.media.MediaRecorder
import android.os.Build
import java.io.File
import java.io.IOException

class AudioRecorder(private val context: Context) {

    private var mediaRecorder: MediaRecorder? = null
    private var audioFile: File? = null

    // 녹음 시작
    fun startRecording(): File? {
        // 앱 내부 캐시 폴더에 고유한 임시 오디오 파일 생성 (voice_시간값.m4a)
        audioFile = File(
            context.cacheDir,
            "voice_${System.currentTimeMillis()}.m4a"
        )

        mediaRecorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(context)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }.apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            setAudioSamplingRate(16000)
            setAudioEncodingBitRate(64000)
            setAudioChannels(1)
            setOutputFile(audioFile?.absolutePath)

            try {
                prepare()
                start()
            } catch (e: IOException) {
                e.printStackTrace()
                return null
            } catch (e: IllegalStateException) {
                e.printStackTrace()
                return null
            }
        }

        return audioFile
    }

    // 녹음 중단
    fun stopRecording(): File? {
        return try {
            mediaRecorder?.apply {
                stop()
                release()
            }
            mediaRecorder = null
            audioFile
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }
}