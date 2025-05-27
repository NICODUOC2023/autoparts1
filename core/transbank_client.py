from django.conf import settings
from transbank.common.options import WebpayOptions
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_type import IntegrationType
from transbank.webpay.webpay_plus.transaction import Transaction

# Lee de settings o usa los valores por defecto de TEST
options = WebpayOptions(
    IntegrationCommerceCodes.WEBPAY_PLUS,  # 597055555532
    IntegrationApiKeys.WEBPAY,             # 579B532A7440BB0C9079…
    IntegrationType.TEST                   # ← must be the enum
)
webpay = Transaction(options)
