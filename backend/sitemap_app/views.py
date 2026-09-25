from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import SitemapGenerator, WireframeGenerator
from .serializers import PromptSerializer, SitemapUpdateSerializer
from core.config import config
import json


@csrf_exempt
@api_view(['POST'])
def init_brief(request):
    """Initialize a brief with dynamic questions based on prompt"""
    prompt = request.data.get('prompt', '')
    ai_enabled = request.data.get('ai_enabled', None)
    if isinstance(ai_enabled, str):
        ai_enabled = ai_enabled.lower() in ('1', 'true', 'yes', 'on')
    generator = SitemapGenerator()
    questions = generator.generate_questions_for_brief(prompt, ai_enabled)
    parsed = generator.parse_prompt(prompt)

    return Response({
        'success': True,
        'questions': questions,
        'parsed': parsed,
        'ai_error': generator.last_ai_error
    }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
def generate_sitemap(request):
    """Generate sitemap from natural language prompt or brief data"""
    prompt = request.data.get('prompt', '')
    brief_data = request.data.get('brief_data')

    generator = SitemapGenerator()
    sitemap_data = generator.generate_sitemap(prompt, brief_data)

    return Response({
        'success': True,
        'sitemap': sitemap_data
    }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
def update_sitemap(request):
    """Update sitemap data"""
    serializer = SitemapUpdateSerializer(data=request.data)

    if serializer.is_valid():
        sitemap_data = serializer.validated_data['sitemap_data']
        return Response({
            'success': True,
            'sitemap': sitemap_data
        }, status=status.HTTP_200_OK)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
def export_json(request):
    """Export sitemap as JSON file"""
    sitemap_data = request.data.get('sitemap_data')

    if not sitemap_data:
        return Response({
            'success': False,
            'error': 'No sitemap data provided'
        }, status=status.HTTP_400_BAD_REQUEST)

    response = HttpResponse(
        json.dumps(sitemap_data, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = 'attachment; filename="sitemap.json"'
    return response


@csrf_exempt
@api_view(['POST'])
def generate_wireframe(request):
    """Generate wireframes from sitemap data"""
    sitemap_data = request.data.get('sitemap_data')

    if not sitemap_data:
        return Response({
            'success': False,
            'error': 'No sitemap data provided'
        }, status=status.HTTP_400_BAD_REQUEST)

    generator = WireframeGenerator()
    wireframes = generator.generate_wireframes(sitemap_data)

    return Response({
        'success': True,
        'wireframes': wireframes
    }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
def regenerate_section(request):
    """Regenerate a specific section description"""
    section_title = request.data.get('title', '')
    section_type = request.data.get('type', 'content')

    generator = WireframeGenerator()
    new_description = generator.regenerate_section_description(section_title, section_type)

    return Response({
        'success': True,
        'description': new_description
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_config(request):
    """Get configuration for frontend"""
    try:
        return Response({
            'success': True,
            'private_key': config.private_key,
            'ai': {
                'chat': {
                    'enabled': config.chat_ai_enabled,
                    'model': config.chat_ai_model,
                    'base_url': config.chat_ai_base_url
                },
                'wireframe': {
                    'model': config.wireframe_ai_model,
                    'base_url': config.wireframe_ai_base_url
                }
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
