from enum import Enum
from typing import Dict, List, Any
from dataclasses import dataclass

class ScoringPlatform(str, Enum):
    TRADE_DESK = "trade_desk"
    PULSEPOINT = "pulsepoint"

class CampaignGoal(str, Enum):
    AWARENESS = "awareness"
    ACTION = "action"

class Channel(str, Enum):
    CTV = "ctv"
    DISPLAY = "display"
    VIDEO = "video"
    AUDIO = "audio"

@dataclass
class MetricConfig:
    name: str
    weight: float
    is_higher_better: bool
    required: bool = True
    
@dataclass
class ScoringConfig:
    platform: ScoringPlatform
    goal: CampaignGoal
    channel: Channel
    ctr_sensitivity: bool
    analysis_level: str
    metrics: List[MetricConfig]
    required_fields: List[str]

class ScoringConfigManager:
    """Manages scoring configurations for different platform/goal/channel combinations"""
    
    @staticmethod
    def get_trade_desk_display_awareness(ctr_sensitivity: bool = False) -> ScoringConfig:
        """Trade Desk Display Awareness scoring configuration"""
        if ctr_sensitivity:
            metrics = [
                MetricConfig("cpm", 0.10, False),  # Lower is better
                MetricConfig("ias_display_fully_in_view_1s_rate", 0.25, True),
                MetricConfig("ctr", 0.30, True),  # Increased for CTR sensitivity
                MetricConfig("ad_load_xl_rate", 0.15, False),  # Lower is better
                MetricConfig("ad_refresh_below_15s_rate", 0.20, False)  # Lower is better
            ]
        else:
            metrics = [
                MetricConfig("cpm", 0.15, False),
                MetricConfig("ias_display_fully_in_view_1s_rate", 0.25, True),
                MetricConfig("ctr", 0.20, True),
                MetricConfig("ad_load_xl_rate", 0.20, False),
                MetricConfig("ad_refresh_below_15s_rate", 0.20, False)
            ]
        
        return ScoringConfig(
            platform=ScoringPlatform.TRADE_DESK,
            goal=CampaignGoal.AWARENESS,
            channel=Channel.DISPLAY,
            ctr_sensitivity=ctr_sensitivity,
            analysis_level="domain",
            metrics=metrics,
            required_fields=[
                "Site", "Supply Vendor", "Advertiser Cost", "Impressions", 
                "Advertiser CPM", "Clicks", "CTR", "IAS Display Fully In View 1 Second Rate",
                "Ad Load - XL (Excessive) - Impressions", "Ad Refresh - Below 15s - Impressions",
                "All Last Click + View Conversion Rate"
            ]
        )
    
    @staticmethod
    def get_trade_desk_display_action() -> ScoringConfig:
        """Trade Desk Display Action scoring configuration"""
        metrics = [
            MetricConfig("cpm", 0.10, False),
            MetricConfig("ias_display_fully_in_view_1s_rate", 0.10, True),
            MetricConfig("conversion_rate", 0.30, True),
            MetricConfig("ctr", 0.15, True),
            MetricConfig("ad_load_xl_rate", 0.15, False),
            MetricConfig("ad_refresh_below_15s_rate", 0.20, False)
        ]
        
        return ScoringConfig(
            platform=ScoringPlatform.TRADE_DESK,
            goal=CampaignGoal.ACTION,
            channel=Channel.DISPLAY,
            ctr_sensitivity=False,
            analysis_level="domain",
            metrics=metrics,
            required_fields=[
                "Site", "Supply Vendor", "Advertiser Cost", "Impressions",
                "Advertiser CPM", "Clicks", "CTR", "IAS Display Fully In View 1 Second Rate",
                "Ad Load - XL (Excessive) - Impressions", "Ad Refresh - Below 15s - Impressions",
                "All Last Click + View Conversion Rate"
            ]
        )
    
    @staticmethod
    def get_trade_desk_ctv() -> ScoringConfig:
        """Trade Desk CTV scoring configuration"""
        metrics = [
            MetricConfig("tv_quality_index_rate", 0.70, True),
            MetricConfig("unique_id_ratio", 0.30, True)
        ]
        
        return ScoringConfig(
            platform=ScoringPlatform.TRADE_DESK,
            goal=CampaignGoal.AWARENESS,  # CTV uses fixed weights regardless of goal
            channel=Channel.CTV,
            ctr_sensitivity=False,
            analysis_level="supply_vendor",
            metrics=metrics,
            required_fields=[
                "Supply Vendor", "Advertiser Cost", "Impressions", "CPM",
                "TV Quality Index", "Unique IDs"
            ]
        )
    
    @staticmethod
    def get_trade_desk_video_audio() -> ScoringConfig:
        """Trade Desk Video/Audio scoring configuration"""
        metrics = [
            MetricConfig("cpm", 0.10, False),
            MetricConfig("sampled_in_view_rate", 0.20, True),
            MetricConfig("player_completion_rate", 0.35, True),
            MetricConfig("player_errors_rate", 0.20, False),
            MetricConfig("player_mute_rate", 0.15, False)
        ]
        
        return ScoringConfig(
            platform=ScoringPlatform.TRADE_DESK,
            goal=CampaignGoal.AWARENESS,  # Fixed weights for video/audio
            channel=Channel.VIDEO,  # Same for audio
            ctr_sensitivity=False,
            analysis_level="domain",
            metrics=metrics,
            required_fields=[
                "Site", "Supply Vendor", "Advertiser Cost", "Impressions", "CPM",
                "Sampled In-View Rate", "Player Completion Rate", "Player Errors", "Player Mute"
            ]
        )
    
    @staticmethod
    def get_pulsepoint_display_awareness() -> ScoringConfig:
        """PulsePoint Display Awareness scoring configuration"""
        metrics = [
            MetricConfig("ecpm", 0.35, False),  # Lower is better
            MetricConfig("ctr", 0.40, True),
            MetricConfig("conversion_rate", 0.25, True)
        ]
        
        return ScoringConfig(
            platform=ScoringPlatform.PULSEPOINT,
            goal=CampaignGoal.AWARENESS,
            channel=Channel.DISPLAY,
            ctr_sensitivity=False,
            analysis_level="domain",
            metrics=metrics,
            required_fields=["Domain", "Total Spend", "Impressions", "eCPM", "CTR", "Conversions"]
        )
    
    @staticmethod
    def get_pulsepoint_display_action() -> ScoringConfig:
        """PulsePoint Display Action scoring configuration"""
        metrics = [
            MetricConfig("ecpm", 0.15, False),
            MetricConfig("ctr", 0.25, True),
            MetricConfig("conversion_rate", 0.60, True)
        ]
        
        return ScoringConfig(
            platform=ScoringPlatform.PULSEPOINT,
            goal=CampaignGoal.ACTION,
            channel=Channel.DISPLAY,
            ctr_sensitivity=False,
            analysis_level="domain",
            metrics=metrics,
            required_fields=["Domain", "Total Spend", "Impressions", "eCPM", "CTR", "Conversions"]
        )
    
    @staticmethod
    def get_pulsepoint_video() -> ScoringConfig:
        """PulsePoint Video scoring configuration (fixed weights regardless of goal)"""
        metrics = [
            MetricConfig("ecpm", 0.20, False),
            MetricConfig("ctr", 0.10, True),
            MetricConfig("completion_rate", 0.50, True),
            MetricConfig("conversion_rate", 0.20, True)
        ]
        
        return ScoringConfig(
            platform=ScoringPlatform.PULSEPOINT,
            goal=CampaignGoal.AWARENESS,  # Fixed weights for video
            channel=Channel.VIDEO,
            ctr_sensitivity=False,
            analysis_level="domain",
            metrics=metrics,
            required_fields=[
                "Domain", "Total Spend", "Impressions", "eCPM", "CTR", 
                "Completion Rate", "Conversions"
            ]
        )
    
    @staticmethod
    def get_config(
        platform: ScoringPlatform,
        goal: CampaignGoal,
        channel: Channel,
        ctr_sensitivity: bool = False
    ) -> ScoringConfig:
        """Get scoring configuration based on platform, goal, and channel"""
        
        if platform == ScoringPlatform.TRADE_DESK:
            if channel == Channel.DISPLAY:
                if goal == CampaignGoal.AWARENESS:
                    return ScoringConfigManager.get_trade_desk_display_awareness(ctr_sensitivity)
                else:
                    return ScoringConfigManager.get_trade_desk_display_action()
            elif channel == Channel.CTV:
                return ScoringConfigManager.get_trade_desk_ctv()
            elif channel in [Channel.VIDEO, Channel.AUDIO]:
                return ScoringConfigManager.get_trade_desk_video_audio()
                
        elif platform == ScoringPlatform.PULSEPOINT:
            if channel == Channel.DISPLAY:
                if goal == CampaignGoal.AWARENESS:
                    return ScoringConfigManager.get_pulsepoint_display_awareness()
                else:
                    return ScoringConfigManager.get_pulsepoint_display_action()
            elif channel == Channel.VIDEO:
                return ScoringConfigManager.get_pulsepoint_video()
        
        raise ValueError(f"Unsupported configuration: {platform}, {goal}, {channel}")

# Mapping of column name variations to standardized names
COLUMN_MAPPINGS = {
    # Trade Desk mappings
    "advertiser_cost": ["Advertiser Cost", "Cost", "Spend", "Total Cost"],
    "advertiser_cpm": ["Advertiser CPM", "CPM", "eCPM"],
    "ias_display_fully_in_view_1s_rate": [
        "IAS Display Fully In View 1 Second Rate", "Viewability Rate", "In View Rate"
    ],
    "ad_load_xl_rate": ["Ad Load - XL (Excessive) - Impressions", "Ad Load XL", "Excessive Ad Load"],
    "ad_refresh_below_15s_rate": ["Ad Refresh - Below 15s - Impressions", "Ad Refresh Below 15s"],
    "conversion_rate": ["All Last Click + View Conversion Rate", "Conversion Rate", "Conv Rate"],
    "sampled_in_view_rate": ["Sampled In-View Rate", "In View Rate"],
    "player_completion_rate": ["Player Completion Rate", "Completion Rate"],
    "player_errors": ["Player Errors", "Errors"],
    "player_mute": ["Player Mute", "Mute Rate"],
    "tv_quality_index": ["TV Quality Index", "Quality Index"],
    "unique_ids": ["Unique IDs", "Unique Identifiers"],
    
    # PulsePoint mappings
    "total_spend": ["Total Spend", "Spend", "Cost"],
    "ecpm": ["eCPM", "CPM"],
    "completion_rate": ["Completion Rate", "Video Completion Rate"],
    
    # Common mappings
    "impressions": ["Impressions", "Imps"],
    "clicks": ["Clicks", "Click"],
    "ctr": ["CTR", "Click Through Rate", "Click-Through Rate"],
    "conversions": ["Conversions", "Conv", "Actions"],
    "domain": ["Domain", "Site", "Publisher", "App Bundle"],
    "supply_vendor": ["Supply Vendor", "SSP", "Exchange"]
} 