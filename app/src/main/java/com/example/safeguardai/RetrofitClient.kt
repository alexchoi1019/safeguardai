package com.example.safeguardai

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {
    // 실제 PC의 로컬 IP 주소 (Wi-Fi 연결 시 실물 기기용)
    private const val BASE_URL = "http://172.30.1.92:8000/"

    val instance: ApiService by lazy {
        val retrofit = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        retrofit.create(ApiService::class.java)
    }
}