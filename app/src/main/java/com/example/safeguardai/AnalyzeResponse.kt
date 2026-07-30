package com.example.safeguardai

import com.google.gson.annotations.SerializedName

data class AnalyzeResponse(
    @SerializedName("status") val status: String,
    @SerializedName("text") val text: String,
    @SerializedName("risk_score") val riskScore: Float,
    @SerializedName("is_phishing") val isPhishing: Boolean
)