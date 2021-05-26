import os


def retrieve_config(service_name: str):
    """The configuration is retrieved from environment variables.

    :param service_name Is used as service identifier and database name.
    """
    config = {
        "name": service_name,
        "database": {
            "type": os.getenv("DB_TYPE", "postgres"),
            "setup": os.getenv("DB_SETUP", False),
            "connection": {
                "host": os.getenv("DB_HOST", "127.0.0.1"),
                "database": os.getenv("DB_IDENTIFIER", service_name),
                "user": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASS", "")
            }
        },
    }
    if os.getenv("ENVIRONMENT", "development") == "development":
        config['dev'] = {
            "host": os.getenv("DEV_HOST", "127.0.0.1"),
            "port": os.getenv("DEV_PORT", 5000)
        }
    return config
