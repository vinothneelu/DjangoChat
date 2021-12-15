def validate_user(context):
    user = context.user

    if user.is_anonymous:
        raise Exception('Authentication Failure: Your must be signed in')
    else:
        return user
