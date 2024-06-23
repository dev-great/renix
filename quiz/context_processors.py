def user_info(request):
    user_info = {
        'user': request.user,
    }
    return {'user_info': user_info}
