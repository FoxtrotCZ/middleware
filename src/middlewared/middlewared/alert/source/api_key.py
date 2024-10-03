import json

from middlewared.alert.base import Alert, AlertClass, SimpleOneShotAlertClass, AlertCategory, AlertLevel


class ApiKeyRevokedAlertClass(AlertClass, SimpleOneShotAlertClass):
    category = AlertCategory.SYSTEM
    level = AlertLevel.WARNING
    title = "API Key Revoked"
    text = (
        "The following API keys have been revoked and must either be renewed or deleted. "
        "Once the maintenance is complete, API client configuration must be updated to "
        "use the renwed API key.\n%(keys)s"
    )

    async def create(self, args):
        return Alert(DeprecatedServiceConfigurationAlertClass, args, key=args['config'])

    async def delete(self, alerts, query):
        return list(filter(
            lambda alert: json.loads(alert.key) != str(query),
            alerts
        ))
