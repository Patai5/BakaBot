from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from constants import FeaturesType
from disnake.ext.commands import InteractionBot

FeatureCallableType = Callable[[InteractionBot], Awaitable[None]]


class FeatureManager:
    """Manages all features of the bot in an event-driven way."""

    def __init__(self):
        self.features: dict[FeaturesType, Feature] = {}

    def register_feature(self, feature: Feature):
        """Registers a feature with its initialization logic."""
        self.features[feature.name] = feature

    async def initialize(self, client: InteractionBot):
        """Initializes all registered features."""
        features = (feature.maybeStart(client) for feature in self.features.values())
        await asyncio.gather(*features)

    async def maybe_start_feature(self, featureName: FeaturesType, client: InteractionBot):
        """Starts a feature by its name if it's not already started."""
        feature = self.features.get(featureName)
        if not feature:
            raise ValueError(f"Feature {feature} is not registered.")

        await feature.maybeStart(client)


class Feature:
    """Represents a feature of the bot."""

    def __init__(self, name: FeaturesType, canStart: Callable[..., bool], initializer: FeatureCallableType):
        self.name: FeaturesType = name
        self.canStart = canStart
        """A function that returns whether the feature can be started."""
        self.initializer = initializer

        self.isStarted = False

    async def maybeStart(self, client: InteractionBot):
        """Starts the feature if it can be started and it's not already running."""
        canStart = self.canStart() and not self.isStarted
        if canStart:
            self.isStarted = True
            await self.initializer(client)
