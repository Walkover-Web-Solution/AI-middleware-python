import jwt

def generateToken(payload, accessKey):
    """Create a JWT token using HS256 with the provided access key."""
    try:
        return jwt.encode(payload, accessKey, algorithm="HS256")
    except Exception as error:
        print("Error generating token:", error)
        raise Exception('Failed to generate token')

# Assuming you want to export it in a similar way to how ES6 modules work
generateTokenModule = {
    "generateToken": generateToken
}
