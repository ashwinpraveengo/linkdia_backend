from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import redirect

# Create your views here.

def home_view(request):
    """
    Simple home view that provides API information
    """
    if request.method == 'GET':
        return JsonResponse({
            'message': 'Welcome to Linkdia API',
            'version': '1.0',
            'endpoints': {
                'graphql': '/graphql/',
                'admin': '/admin/',
                'accounts': '/accounts/'
            },
            'graphql_playground': '/graphql/'
        })
    elif request.method == 'POST':
        # Redirect POST requests to GraphQL endpoint
        return redirect('/graphql/')
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
