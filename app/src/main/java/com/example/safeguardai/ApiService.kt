package com.example.safeguardai

import okhttp3.MultipartBody
import retrofit2.Call
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

interface ApiService {
    @Multipart
    @POST("/analyze-audio")
    fun analyzeAudio(
        @Part file: MultipartBody.Part
    ): Call<AnalyzeResponse>
}