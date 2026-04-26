"""
Asset Classifier — Type Detection Layer

Takes a CanonicalAsset from the Entity Resolver and classifies it into one of
three types. This classification determines which signal layers are executed
in the multi-layer risk engine.

Asset Types:
  - smart_contract_token: Has a contract address on an EVM chain → all 4 layers
  - native_asset: BTC, ETH, XRP, etc. (no contract) → market + audit fallback + regulatory
  - low_data_asset: Minimal CoinGecko data → market (limited) + regulatory
"""

import logging
from typing import Dict, Any, List
from backend.services.entity_resolver import CanonicalAsset, EVM_CHAINS

logger = logging.getLogger(__name__)


class AssetType:
    SMART_CONTRACT_TOKEN = "smart_contract_token"
    NATIVE_ASSET = "native_asset"
    LOW_DATA_ASSET = "low_data_asset"


class SignalLayerConfig:
    """
    Defines which signal layers are applicable based on asset type.
    """

    def __init__(
        self,
        structural: bool = False,
        market: bool = True,
        audit: bool = True,
        regulatory: bool = True,
        structural_mode: str = "not_applicable",
        audit_mode: str = "full",
        market_mode: str = "full",
    ):
        self.structural = structural
        self.market = market
        self.audit = audit
        self.regulatory = regulatory
        self.structural_mode = structural_mode  # "full" | "not_applicable"
        self.audit_mode = audit_mode            # "full" | "fallback"
        self.market_mode = market_mode          # "full" | "limited"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "structural": self.structural,
            "market": self.market,
            "audit": self.audit,
            "regulatory": self.regulatory,
            "structural_mode": self.structural_mode,
            "audit_mode": self.audit_mode,
            "market_mode": self.market_mode,
        }


# Layer configuration per asset type
LAYER_CONFIGS = {
    AssetType.SMART_CONTRACT_TOKEN: SignalLayerConfig(
        structural=True,
        market=True,
        audit=True,
        regulatory=True,
        structural_mode="full",
        audit_mode="full",
        market_mode="full",
    ),
    AssetType.NATIVE_ASSET: SignalLayerConfig(
        structural=False,
        market=True,
        audit=True,
        regulatory=True,
        structural_mode="not_applicable",
        audit_mode="fallback",
        market_mode="full",
    ),
    AssetType.LOW_DATA_ASSET: SignalLayerConfig(
        structural=False,
        market=True,
        audit=False,
        regulatory=True,
        structural_mode="not_applicable",
        audit_mode="fallback",
        market_mode="limited",
    ),
}


class AssetClassifier:
    """
    Classifies a CanonicalAsset and returns the applicable signal layer configuration.
    """

    def classify(self, asset: CanonicalAsset) -> str:
        """
        Determine the asset type based on the canonical asset properties.
        """
        if not asset.resolved:
            if asset.contract_address:
                return AssetType.SMART_CONTRACT_TOKEN
            return AssetType.LOW_DATA_ASSET

        # 1. Any asset with a contract address is a smart_contract_token
        if asset.contract_address:
            logger.info(f"AssetClassifier: '{asset.name}' (chain: {asset.chain}) → smart_contract_token")
            return AssetType.SMART_CONTRACT_TOKEN

        # 2. Native assets (BTC, ETH, XRP, etc.)
        if not asset.contract_address:
            # If it has a rank or significant market presence, it's a full native asset
            if asset.market_cap_rank is not None or asset.market_presence in ["Established", "Mid-tier", "Active"]:
                logger.info(f"AssetClassifier: '{asset.name}' → native_asset")
                return AssetType.NATIVE_ASSET
            
            # Low data native asset
            logger.info(f"AssetClassifier: '{asset.name}' → low_data_asset (minimal native presence)")
            return AssetType.LOW_DATA_ASSET

        return AssetType.LOW_DATA_ASSET

    def get_layer_config(self, asset_type: str) -> SignalLayerConfig:
        """
        Returns the signal layer configuration for the given asset type.
        """
        config = LAYER_CONFIGS.get(asset_type, LAYER_CONFIGS[AssetType.LOW_DATA_ASSET])
        logger.info(f"AssetClassifier: Layer config for '{asset_type}': {config.to_dict()}")
        return config

    def classify_and_configure(self, asset: CanonicalAsset) -> tuple:
        """
        Convenience method: classify the asset and return both the type and config.

        Returns:
            (asset_type: str, layer_config: SignalLayerConfig)
        """
        asset_type = self.classify(asset)
        layer_config = self.get_layer_config(asset_type)
        return asset_type, layer_config
