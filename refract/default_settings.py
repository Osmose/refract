import os


GA_TRACKING_ID = os.environ.get('REFRACT_GA_TRACKING_ID', '')

# Keys used for generating Chrome CRX files.
PRIVATE_KEY = os.environ.get('REFRACT_PRIVATE_KEY', '')  # .pem
