import secrets

def generate_token(prefix="org_", length=35):
    return prefix + secrets.token_hex(length // 2)

