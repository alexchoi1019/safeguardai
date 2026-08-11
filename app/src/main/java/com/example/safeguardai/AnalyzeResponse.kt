package com.example.safeguardai

import com.google.gson.annotations.SerializedName

data class AnalyzeResponse(
    @SerializedName("status") val status: String,
    @SerializedName("text") val text: String,
    @SerializedName("risk_score") val riskScore: Float,
    @SerializedName("is_phishing") val isPhishing: Boolean,
    
    @SerializedName("detected_categories") 
    val detectedCategories: List<String> = emptyList(),
    
    @SerializedName("detected_keywords") 
    val detectedKeywords: List<String> = emptyList(),
    
    @SerializedName("reasons") 
    val reasons: List<String> = emptyList(),

    @SerializedName("actions")
    val actions: List<String> = emptyList(),
    
    @SerializedName("processing_time")
    val processingTime: Float? = null
)
