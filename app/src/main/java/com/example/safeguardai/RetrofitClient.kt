package com.example.safeguardai

import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {
    /**
     * 서버 주소 설정 가이드:
     * 1. 안드로이드 에뮬레이터 사용 시: "http://10.0.2.2:8000/"
     * 2. 실물 기기(폰) 사용 시: "http://PC의_IP주소:8000/" (PC와 폰이 같은 Wi-Fi에 연결되어야 함)
     */
    private const val BASE_URL = "http://172.30.1.92:8000/"

    val instance: ApiService by lazy {
        // Whisper 모델의 분석 시간이 길어질 수 있으므로 타임아웃을 충분히 늘립니다. (Day 10 안정화 스펙)
        val okHttpClient = OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS)
            .callTimeout(150, TimeUnit.SECONDS)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        retrofit.create(ApiService::class.java)
    }
}
