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
    try:
        prompt = request.data.get('prompt', '')
        brief_data = request.data.get('brief_data')

        generator = SitemapGenerator()
        sitemap_data = generator.generate_sitemap(prompt, brief_data)

        # Database persistence if available
        sitemap_id = None
        try:
            from .models import Sitemap
            record = Sitemap.objects.create(
                prompt=prompt or 'Generated Sitemap',
                website_type=sitemap_data.get('website_type', 'Website'),
                sitemap_data=sitemap_data
            )
            sitemap_id = record.id
        except Exception:
            pass

        return Response({
            'success': True,
            'sitemap': sitemap_data,
            'sitemap_id': sitemap_id
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def update_sitemap(request):
    """Update sitemap data"""
    try:
        serializer = SitemapUpdateSerializer(data=request.data)

        if serializer.is_valid():
            sitemap_data = serializer.validated_data['sitemap_data']
            sitemap_id = None
            try:
                from .models import Sitemap
                record = Sitemap.objects.create(
                    prompt=sitemap_data.get('brief', {}).get('description') or sitemap_data.get('website_type', 'Updated Sitemap'),
                    website_type=sitemap_data.get('website_type', 'Website'),
                    sitemap_data=sitemap_data
                )
                sitemap_id = record.id
            except Exception:
                pass

            return Response({
                'success': True,
                'sitemap': sitemap_data,
                'sitemap_id': sitemap_id
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    """Generate wireframes from sitemap data (supports all pages or specific page_id)"""
    try:
        sitemap_data = request.data.get('sitemap_data')
        page_id = request.data.get('page_id')

        if not sitemap_data:
            return Response({
                'success': False,
                'error': 'No sitemap data provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        generator = WireframeGenerator()
        wireframes = generator.generate_wireframes(sitemap_data, page_id=page_id)

        return Response({
            'success': True,
            'wireframes': wireframes
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def regenerate_section(request):
    """Regenerate a specific section description or full section structure"""
    try:
        section_title = request.data.get('title', '')
        section_type = request.data.get('type', 'content')
        page_context = request.data.get('page_context')
        brief = request.data.get('brief')

        generator = WireframeGenerator()
        new_description = generator.regenerate_section_description(section_title, section_type)
        section_obj = generator.service.regenerate_section(
            section_title, section_type, page_context=page_context, brief=brief
        )

        return Response({
            'success': True,
            'description': new_description,
            'section': section_obj
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def evaluate_quality(request):
    """
    Evaluate the generation quality of a wireframe container across 8 dimensions.
    Returns overall score (0-100), letter grade (A+, A, B, C, F), and issues/recommendations.
    """
    try:
        from .quality_evaluator import QualityEvaluator
        wireframe_data = request.data.get('wireframe_data') or request.data.get('wireframes')
        sitemap_data = request.data.get('sitemap_data')

        if not wireframe_data:
            return Response({
                'success': False,
                'error': 'wireframe_data is required for quality evaluation'
            }, status=status.HTTP_400_BAD_REQUEST)

        evaluator = QualityEvaluator()
        report = evaluator.evaluate(wireframe_data, sitemap_data)

        return Response({
            'success': True,
            'report': report.to_dict()
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_config(request):
    """Get configuration for frontend without exposing sensitive secrets."""
    try:
        from .providers import get_ai_provider, OllamaProvider, OpenRouterProvider
        active_provider = get_ai_provider()
        ollama_avail = OllamaProvider().is_available()
        openrouter_avail = OpenRouterProvider().is_available()

        return Response({
            'success': True,
            'provider': config.ai_provider,
            'active_provider': active_provider.name,
            'has_api_key': bool(config.openrouter_api_key),
            'private_key': None,  # Secrets are never exposed to the client
            'ai': {
                'provider': config.ai_provider,
                'chat': {
                    'enabled': config.chat_ai_enabled,
                    'model': config.openrouter_model if active_provider.name == 'openrouter' else config.ollama_model,
                    'base_url': config.openrouter_base_url if active_provider.name == 'openrouter' else config.ollama_base_url
                },
                'wireframe': {
                    'model': config.wireframe_ai_model if active_provider.name == 'openrouter' else config.ollama_model,
                    'base_url': config.wireframe_ai_base_url if active_provider.name == 'openrouter' else config.ollama_base_url
                },
                'ollama': {
                    'available': ollama_avail,
                    'model': config.ollama_model
                },
                'openrouter': {
                    'available': openrouter_avail,
                    'model': config.openrouter_model
                }
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
