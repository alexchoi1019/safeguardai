package com.example.safeguardai

import com.google.gson.annotations.SerializedName
import java.io.Serializable

data class RiskFactor(
    @SerializedName("category")
    val category: String,

    @SerializedName("label")
    val label: String,

    @SerializedName("score")
    val score: Float
) : Serializable

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

    @SerializedName("risk_factors")
    val riskFactors: List<RiskFactor> = emptyList(),
    
    @SerializedName("processing_time")
    val processingTime: Float? = null
) : Serializable
