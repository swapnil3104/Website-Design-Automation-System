import re
import uuid
import json
import time
import urllib.request
import urllib.error
from typing import Dict, List, Any
from core.config import config

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class SitemapGenerator:
    """Service class for generating sitemaps from natural language prompts"""
    
    def __init__(self):
        self.last_ai_error = None
        # Common page types and their typical sections
        self.page_types = {
            'home': {
                'sections': ['navbar', 'hero', 'features', 'benefits', 'testimonials', 'cta'],
                'description': 'Main landing page with company overview and key information'
            },
            'about': {
                'sections': ['navbar', 'hero', 'story', 'team', 'values'],
                'description': 'Company background, history, and team information'
            },
            'services': {
                'sections': ['navbar', 'hero', 'services-grid', 'process', 'pricing'],
                'description': 'Services and solutions offered by the company'
            },
            'products': {
                'sections': ['navbar', 'hero', 'product-grid', 'features', 'comparison'],
                'description': 'Product catalog and detailed information'
            },
            'portfolio': {
                'sections': ['navbar', 'hero', 'gallery', 'case-studies', 'process'],
                'description': 'Showcase of work, projects, and case studies'
            },
            'blog': {
                'sections': ['navbar', 'hero', 'blog-grid', 'categories', 'recent-posts'],
                'description': 'Blog posts, articles, and company news'
            },
            'contact': {
                'sections': ['navbar', 'hero', 'contact-form', 'location', 'info'],
                'description': 'Contact information, form, and office locations'
            },
            'pricing': {
                'sections': ['navbar', 'hero', 'pricing-table', 'features', 'faq'],
                'description': 'Pricing plans and package information'
            }
        }

        self.intent_hints = {
            'sports': {
                'keywords': ['tournament', 'league', 'fixtures', 'standings', 'points table', 'live score', 'score updates', 'match results', 'cricket', 'football', 'soccer', 'basketball'],
                'type': 'Sports Tournament Website',
                'pages': ['Home', 'Team Registration', 'Fixtures', 'Live Scores', 'Points Table', 'Player Statistics', 'Match Results', 'About', 'Contact']
            },
            'media': {
                'keywords': ['movie', 'movies', 'film', 'cinema', 'imdb', 'tmdb', 'omdb', 'watchlist', 'trending'],
                'type': 'Movie Finder Website',
                'pages': ['Home', 'Trending Movies', 'Favorites', 'About', 'Contact']
            },
            'marketing': {
                'keywords': ['marketing', 'agency', 'creative', 'branding'],
                'type': 'Marketing Agency Website',
                'pages': ['Home', 'Services', 'Portfolio', 'About', 'Contact']
            },
            'legal': {
                'keywords': ['law', 'legal', 'attorney', 'lawyer'],
                'type': 'Legal Services Website',
                'pages': ['Home', 'Practice Areas', 'Attorneys', 'About', 'Contact']
            },
            'food': {
                'keywords': ['restaurant', 'food', 'cafe', 'bakery', 'dining', 'recipe', 'recipes', 'cooking'],
                'type': 'Restaurant Website',
                'pages': ['Home', 'Menu', 'About', 'Reservations', 'Contact']
            },
            'recipe': {
                'keywords': ['recipe', 'recipes', 'cooking', 'meal prep', 'ingredients', 'kitchen'],
                'type': 'Recipe Website',
                'pages': ['Home', 'Recipe Search', 'Categories', 'Favorites', 'About', 'Contact']
            },
            'ecommerce': {
                'keywords': ['shop', 'store', 'ecommerce', 'cart', 'checkout'],
                'type': 'Ecommerce Website',
                'pages': ['Home', 'Products', 'Cart', 'Account', 'Support']
            },
            'saas': {
                'keywords': ['saas', 'software', 'platform', 'cloud', 'api'],
                'type': 'SaaS Website',
                'pages': ['Home', 'Features', 'Pricing', 'Docs', 'Contact']
            },
            'portfolio': {
                'keywords': ['portfolio', 'designer', 'studio', 'showcase'],
                'type': 'Portfolio Website',
                'pages': ['Home', 'Portfolio', 'Services', 'About', 'Contact']
            },
            'education': {
                'keywords': ['school', 'college', 'university', 'academy', 'course', 'courses', 'learning', 'student', 'instructor', 'enrollment'],
                'type': 'Education Website',
                'pages': ['Home', 'Courses', 'Instructors', 'Student Reviews', 'Enrollment', 'Contact', 'About']
            },
            'health': {
                'keywords': ['clinic', 'hospital', 'health', 'medical', 'dentist'],
                'type': 'Healthcare Website',
                'pages': ['Home', 'Services', 'Doctors', 'About', 'Contact']
            },
            'travel': {
                'keywords': ['flight', 'flights', 'airline', 'airlines', 'booking', 'ticket', 'pnr', 'trip'],
                'type': 'Flight Booking Website',
                'pages': ['Home', 'Flight Search', 'Flight Listing', 'Select Flight', 'Passenger Details', 'Add-ons', 'Checkout', 'Booking Summary', 'Offers', 'Contact']
            }
        }

    def _title_based_section_description(self, title: str, section_type: str, page_name: str, normalized: Dict[str, Any]) -> str:
        title_text = str(title or page_name).strip() or page_name
        page_label = str(page_name or 'this page').strip() or 'this page'
        client = str((normalized or {}).get('client', '') or 'the brand').strip()

        def _brief_list_local(value: Any) -> List[str]:
            if isinstance(value, list):
                return [str(v).strip() for v in value if str(v).strip()][:8]
            if isinstance(value, str):
                return [part.strip() for part in re.split(r'[,\n;/]| and ', value, flags=re.IGNORECASE) if part.strip()][:8]
            return []

        goals = _brief_list_local((normalized or {}).get('goals'))
        services = _brief_list_local((normalized or {}).get('services'))
        features = _brief_list_local((normalized or {}).get('features'))
        focus = goals[0] if goals else (services[0] if services else (features[0] if features else page_label))
        lower_type = str(section_type or 'content').lower()

        if lower_type == 'footer':
            return f'Wraps up {page_label} with useful links, contact routes, and clear next steps for visitors exploring {client}.'
        if lower_type == 'cta':
            return f'Encourages visitors to take the next action after reviewing {title_text}, with messaging tied to {focus}.'
        if lower_type == 'faq':
            return f'Answers practical questions around {title_text} so the {page_label} experience stays clear and decision-ready.'
        if lower_type in ('content', 'information', 'info', 'main-info', 'supporting-info'):
            return f'Explains {title_text} in a way that supports {focus} and gives the {page_label} page more depth and clarity.'
        if lower_type in ('contact', 'contact-form', 'contact-details'):
            return f'Guides visitors through {title_text} with clear ways to reach {client} and move the conversation forward.'
        if lower_type in ('services', 'service'):
            return f'Presents {title_text} as a focused offer connected to {focus}, with practical value for the visitor.'
        if lower_type == 'features':
            return f'Shows how {title_text} strengthens the experience of {page_label} and supports the goals defined in the brief.'
        return f'Keeps {title_text} specific to {page_label} while reinforcing the priorities captured in the original brief.'

    def _detect_intent(self, prompt: str) -> Dict[str, Any]:
        prompt_lower = (prompt or '').lower()
        recipe_hint = self.intent_hints.get('recipe')
        if recipe_hint:
            if re.search(r'\b(recipe|recipes|cooking|meal prep|ingredients)\b', prompt_lower):
                return recipe_hint
        education_hint = self.intent_hints.get('education')
        if education_hint:
            if re.search(r'\b(education|learning|online learning|e-?learning|course|courses|instructor|student|enrollment|academy|university|school)\b', prompt_lower):
                return education_hint
        sports_hint = self.intent_hints.get('sports')
        if sports_hint:
            if re.search(r'\b(tournament|league|fixtures|standings|points table|live score|score updates|match results|cricket|football|soccer|basketball)\b', prompt_lower):
                return sports_hint
        media_hint = self.intent_hints.get('media')
        if media_hint:
            if re.search(r'\b(movie|movies|film|cinema|imdb|tmdb|omdb|watchlist|trending)\b', prompt_lower):
                return media_hint
        travel_hint = self.intent_hints.get('travel')
        if travel_hint:
            if re.search(r'\b(flight|flights|airline|airlines|pnr|ticket|airfare)\b', prompt_lower):
                return travel_hint
            if re.search(r'\b(flight booking|air ticket|domestic flight|round trip|one way trip|one-way trip)\b', prompt_lower):
                return travel_hint
        best = None
        best_score = 0
        for hint in self.intent_hints.values():
            score = 0
            for k in hint['keywords']:
                if k in prompt_lower:
                    score += 1
            if score > best_score:
                best_score = score
                best = hint
        return best or {}

    def _merge_options(self, parsed_value: Any, defaults: List[str]) -> List[str]:
        options: List[str] = []
        if parsed_value:
            if isinstance(parsed_value, list):
                options.extend([str(v).strip() for v in parsed_value if str(v).strip()])
            else:
                parts = [p.strip() for p in re.split(r'[,\|/]| and ', str(parsed_value), flags=re.IGNORECASE) if p.strip()]
                options.extend(parts)
        options.extend(defaults)
        seen = set()
        unique = []
        for opt in options:
            key = opt.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(opt)
        return unique

    def _extract_prompt_keywords(self, prompt: str, parsed: Dict[str, Any]) -> List[str]:
        """Lightweight keyword extraction for offline suggestion fallbacks."""
        text = (prompt or "").lower()
        tokens = re.findall(r"[a-z][a-z0-9]{2,}", text)
        stop = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'build', 'business', 'by', 'can', 'create', 'design',
            'develop', 'do', 'for', 'from', 'get', 'have', 'how', 'i', 'if', 'in', 'include', 'including',
            'it', 'me', 'more', 'new', 'of', 'on', 'or', 'our', 'page', 'pages', 'platform', 'please',
            'provide', 'site', 'system', 'that', 'the', 'their', 'then', 'they', 'this', 'to', 'use',
            'users', 'using', 'want', 'we', 'where', 'will', 'with', 'website', 'web', 'app', 'application'
        }
        keywords: List[str] = []
        for t in tokens:
            if t in stop:
                continue
            if t.isdigit():
                continue
            if t not in keywords:
                keywords.append(t)

        # Prefer structured hints when available
        type_hint = (parsed.get('type') or '').lower()
        type_hint = re.sub(r'\b(website|platform|app|application|system)\b', '', type_hint).strip()
        if type_hint:
            for t in re.findall(r"[a-z][a-z0-9]{2,}", type_hint):
                if t not in stop and t not in keywords:
                    keywords.insert(0, t)

        if isinstance(parsed.get('pages'), list):
            for p in parsed.get('pages'):
                if not isinstance(p, str):
                    continue
                for t in re.findall(r"[a-z][a-z0-9]{2,}", p.lower()):
                    if t in stop:
                        continue
                    if t not in keywords:
                        keywords.append(t)

        return keywords[:12]

    def _fallback_question_options(
        self,
        qid: str,
        prompt: str,
        parsed: Dict[str, Any],
        website_type: str,
        intent: Dict[str, Any],
        travel_mode: bool
    ) -> List[str]:
        """Offline fallback suggestions when AI is unavailable or returns nothing."""
        qid = (qid or '').strip()
        prompt_lower = (prompt or '').lower()
        keywords = self._extract_prompt_keywords(prompt, parsed)

        def _uniq(items: List[str]) -> List[str]:
            seen = set()
            out: List[str] = []
            for it in items:
                s = str(it).strip()
                if not s:
                    continue
                key = s.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(s)
            return out

        def _split_csv(val: Any) -> List[str]:
            if not val:
                return []
            if isinstance(val, list):
                return [str(v).strip() for v in val if str(v).strip()]
            return [p.strip() for p in re.split(r'[,\|/;]| and ', str(val), flags=re.IGNORECASE) if p.strip()]

        pages_list: List[str] = []
        if isinstance(parsed.get('pages'), list):
            pages_list = [str(p).strip() for p in parsed.get('pages') if str(p).strip()]
        elif parsed.get('pages_text'):
            pages_list = _split_csv(parsed.get('pages_text'))

        primary_keyword = (keywords[0] if keywords else 'Nova').strip()
        primary_cap = ' '.join([w.capitalize() for w in primary_keyword.split()]) if primary_keyword else 'Nova'
        second_keyword = keywords[1] if len(keywords) > 1 else ''
        second_cap = ' '.join([w.capitalize() for w in second_keyword.split()]) if second_keyword else ''

        if qid == 'language':
            return ['English']

        if qid == 'client':
            suffixes = ['Hub', 'Studio', 'Labs', 'Works', 'Flow', 'Nest', 'Box', 'Spot', 'Pro', 'HQ']
            ideas: List[str] = []
            base = primary_cap.replace(' ', '')
            if second_cap:
                ideas.append(f"{base}{second_cap.replace(' ', '')}")
            for suf in suffixes:
                ideas.append(f"{base}{suf}")
                if second_cap and len(ideas) < 5:
                    ideas.append(f"{second_cap.replace(' ', '')}{suf}")
                if len(ideas) >= 5:
                    break
            return _uniq(ideas)[:5]

        if qid == 'type':
            primary = (parsed.get('type') or website_type or intent.get('type') or 'Business Website').strip()
            alts: List[str] = [primary]
            if primary.lower().endswith('website'):
                base = primary[: -len('website')].strip()
                if base:
                    alts.extend([f"{base} Platform", f"{base} App", f"{base} System"])
            elif primary.lower().endswith('app'):
                base = primary[: -len('app')].strip()
                if base:
                    alts.extend([f"{base} Website", f"{base} Platform"])
            return _uniq(alts)[:5]

        if qid == 'showcase':
            opts: List[str] = []
            # Restaurant / food experience intent
            if re.search(r'\b(restaurant|cafe|bistro|dining|food|menu|chef|dish|cuisine)\b', prompt_lower):
                opts.extend([
                    'Menu & Signature Dishes',
                    'Table Reservations',
                    'Dining Experience Showcase',
                    'Chef Specials',
                    'Food Gallery'
                ])
            # Ecommerce / shopping intent
            if re.search(r'\b(store|shop|shopping|ecommerce|e-commerce|product|products|collection|catalog|cart|checkout)\b', prompt_lower):
                opts.extend([
                    'Product Browsing & Shopping',
                    'Featured Collections Showcase',
                    'Product Discovery & Filtering',
                    'Personalized Shopping Experience',
                    'Cart & Checkout'
                ])
            if re.search(r'\bsearch\b', prompt_lower):
                opts.append('Search & Discovery')
            if re.search(r'\bfilter\b', prompt_lower):
                opts.append('Filtering & Browsing')
            if re.search(r'\b(book|booking|reserve|reservation|checkout|payment)\b', prompt_lower):
                opts.append('Booking & Checkout')
            if re.search(r'\b(enroll|enrollment|register|registration|sign up|signup)\b', prompt_lower):
                opts.append('Enrollment & Registration')
            if re.search(r'\b(dashboard|admin|manage|management)\b', prompt_lower):
                opts.append('Management Dashboard')
            if not opts:
                base = primary_cap if primary_cap else 'Product'
                opts.extend([
                    f"{base} Showcase",
                    f"{base} Discovery",
                    f"{base} Experience"
                ])
            return _uniq(opts)[:5]

        if qid in ('services', 'features'):
            # Start from any parsed value if present
            parsed_val = parsed.get(qid)
            opts = _split_csv(parsed_val)
            if not opts and parsed.get('features') and qid == 'services':
                opts = _split_csv(parsed.get('features'))
            # Derive from pages
            if pages_list:
                derived = [p for p in pages_list if p.lower() not in ('home', 'about', 'contact')]
                opts.extend(derived)
            # Derive from prompt verbs
            if re.search(r'\bsearch\b', prompt_lower):
                opts.append('Search')
            if re.search(r'\bfilter\b', prompt_lower):
                opts.append('Filters')
            if re.search(r'\b(favorite|favourites|saved)\b', prompt_lower):
                opts.append('Saved Favorites')
            if re.search(r'\b(review|rating|testimonial)\b', prompt_lower):
                opts.append('Reviews & Ratings')
            if re.search(r'\b(profile|account|login|register)\b', prompt_lower):
                opts.append('User Accounts')
            if qid == 'features':
                opts.extend(['Responsive UI', 'Fast Loading', 'Accessible Design'])
            return _uniq(opts)[:5]

        if qid == 'goals':
            noun = (primary_keyword if primary_keyword else 'users')
            noun = noun if noun.endswith('s') else noun + 's'
            opts: List[str] = []
            if re.search(r'\bsearch\b', prompt_lower):
                opts.append(f"Make {noun} discovery fast")
                opts.append("Improve search relevance")
            if re.search(r'\b(book|reserve|checkout)\b', prompt_lower):
                opts.append("Increase successful bookings")
                opts.append("Reduce checkout drop-off")
            if re.search(r'\b(enroll|register|signup)\b', prompt_lower):
                opts.append("Increase sign-ups")
                opts.append("Boost conversion rate")
            if not opts:
                base = primary_cap if primary_cap else (website_type or 'Site')
                opts.extend([
                    f"Improve {base} experience",
                    f"Increase {base} engagement",
                    f"Build trust in {base}"
                ])
            return _uniq(opts)[:5]

        if qid == 'pages':
            # Prefer authoritative parsed pages
            if len(pages_list) >= 3:
                return _uniq(pages_list)
            # Fall back to intent pages if available (only as suggestions)
            if isinstance(intent.get('pages'), list) and intent.get('pages'):
                return _uniq([str(p).strip() for p in intent.get('pages') if str(p).strip()])
            # Prompt-derived baseline
            base = primary_cap if primary_cap else (website_type or 'Site')
            derived = [f"{base} Overview", f"{base} Details", "Contact", "Home"]
            return _uniq(derived)

        if qid in ('style', 'tone'):
            opts: List[str] = []
            if qid == 'style':
                if re.search(r'\bmodern\b', prompt_lower):
                    opts.append('Modern & Clean')
                if re.search(r'\bclean\b', prompt_lower):
                    opts.append('Clean Minimal')
                if re.search(r'\bminimal\b', prompt_lower):
                    opts.append('Minimal')
                if re.search(r'\bwarm\b', prompt_lower):
                    opts.append('Warm & Inviting')
                if re.search(r'\bbold\b', prompt_lower):
                    opts.append('Bold & Graphic')
                if primary_cap:
                    opts.extend([f"{primary_cap} Modern", f"{primary_cap} Minimal"])
                else:
                    opts.extend(['Bright & Friendly', 'Elegant & Premium', 'Dark & Sleek'])
            else:
                if re.search(r'\bfriendly\b', prompt_lower):
                    opts.append('Friendly & Helpful')
                if re.search(r'\bprofessional\b', prompt_lower):
                    opts.append('Professional & Clear')
                if re.search(r'\bplayful\b', prompt_lower):
                    opts.append('Playful & Energetic')
                if re.search(r'\btrust\b|\bsecure\b', prompt_lower):
                    opts.append('Trustworthy & Reassuring')
                if primary_cap:
                    opts.extend([f"{primary_cap} Friendly", f"{primary_cap} Professional"])
            return _uniq(opts)[:5]

        if travel_mode:
            if qid == 'trip_types':
                return ['One-way', 'Round trip', 'Multi-city']
            if qid == 'passenger_types':
                return ['Adult', 'Child', 'Infant']
            if qid == 'addons':
                return ['Seat selection', 'Extra baggage', 'Meals', 'Travel insurance', 'Priority boarding']
            if qid == 'payments':
                return ['UPI', 'Credit/Debit Cards', 'Net Banking', 'Wallets', 'EMI']
            if qid == 'policies':
                return ['Cancellation rules', 'Refund policy', 'Change fees', 'No-show policy', 'GST invoice policy']

        return []

    def _strip_code_fences(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith('```'):
            cleaned = re.sub(r'^```[a-zA-Z]*\n', '', cleaned)
            cleaned = re.sub(r'\n```$', '', cleaned)
        return cleaned.strip()

    def _ai_suggest_options(self, prompt: str, questions: List[Dict], parsed: Dict[str, Any], ai_enabled: Any = None) -> Dict[str, List[str]]:
        self.last_ai_error = None
        enabled = config.chat_ai_enabled if ai_enabled is None else bool(ai_enabled)
        if not enabled:
            return {}
        api_key = config.ai_api_key
        if not api_key:
            return {}

        base_url = config.chat_ai_base_url
        primary_model = config.chat_ai_model
        fallback_models = config.chat_ai_fallback_models
        models = []
        if primary_model:
            models.append(primary_model)
        for m in fallback_models:
            if m and m not in models:
                models.append(m)
        if not models:
            return {}

        compact_questions = [{
            'id': q.get('id'),
            'text': q.get('text')
        } for q in questions]

        question_ids = [q.get('id') for q in questions if q.get('id')]

        def _tokenize(text: str) -> List[str]:
            if not text:
                return []
            return re.findall(r"[a-z][a-z0-9]{2,}", text.lower())

        def _build_context_tokens() -> set:
            tokens = set(self._extract_prompt_keywords(prompt, parsed))
            for key in ('pages', 'services', 'features', 'goals', 'showcase', 'style', 'tone', 'type', 'client'):
                val = parsed.get(key)
                if isinstance(val, list):
                    for item in val:
                        tokens.update(_tokenize(str(item)))
                elif isinstance(val, str):
                    tokens.update(_tokenize(val))
            return tokens

        def _filter_options_by_context(options_map: Dict[str, List[str]]) -> Dict[str, List[str]]:
            context_tokens = _build_context_tokens()
            if not context_tokens:
                return options_map
            filtered: Dict[str, List[str]] = {}
            for qid, opts in options_map.items():
                if not isinstance(opts, list):
                    continue
                if qid == 'language':
                    filtered[qid] = opts
                    continue
                kept: List[str] = []
                for opt in opts:
                    tokens = _tokenize(str(opt))
                    if any(t in context_tokens for t in tokens):
                        kept.append(str(opt).strip())
                if kept:
                    filtered[qid] = kept
            return filtered

        def _parse_ai_json(content: str) -> Dict[str, List[str]]:
            content = self._strip_code_fences(content or '')
            if not content:
                return {}
            try:
                parsed_json = json.loads(content)
            except json.JSONDecodeError:
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1 and end > start:
                    try:
                        parsed_json = json.loads(content[start:end + 1])
                    except json.JSONDecodeError:
                        return {}
                else:
                    return {}
            
            cleaned = {}
            if isinstance(parsed_json, list):
                for idx, item in enumerate(parsed_json):
                    if idx >= len(question_ids):
                        break
                    qid = question_ids[idx]
                    if isinstance(item, list):
                        cleaned[qid] = [str(v).strip() for v in item if str(v).strip()]
                    elif isinstance(item, str):
                        parts = [p.strip() for p in re.split(r'[,\|/;]| and ', item, flags=re.IGNORECASE) if p.strip()]
                        if parts:
                            cleaned[qid] = parts
            elif isinstance(parsed_json, dict):
                if isinstance(parsed_json.get('answers'), list):
                    answers = parsed_json.get('answers')
                    for idx, item in enumerate(answers):
                        if idx >= len(question_ids):
                            break
                        qid = question_ids[idx]
                        if isinstance(item, list):
                            cleaned[qid] = [str(v).strip() for v in item if str(v).strip()]
                        elif isinstance(item, str):
                            parts = [p.strip() for p in re.split(r'[,\|/;]| and ', item, flags=re.IGNORECASE) if p.strip()]
                            if parts:
                                cleaned[qid] = parts
                for key, value in parsed_json.items():
                    if key == 'answers':
                        continue
                    if isinstance(value, list):
                        cleaned[key] = [str(v).strip() for v in value if str(v).strip()]
                    elif isinstance(value, dict) and isinstance(value.get('options'), list):
                        cleaned[key] = [str(v).strip() for v in value.get('options') if str(v).strip()]
                    elif isinstance(value, str):
                        parts = [p.strip() for p in re.split(r'[,\|/;]| and ', value, flags=re.IGNORECASE) if p.strip()]
                        if parts:
                            cleaned[key] = parts

            if cleaned:
                alias_map = {
                    'client': ['client', 'company', 'business', 'brand', 'project', 'project_name', 'business_name', 'site_name', 'name'],
                    'type': ['type', 'business_type', 'website_type', 'site_type', 'project_type'],
                    'showcase': ['showcase', 'primary_function', 'primary goal', 'purpose', 'function'],
                    'services': ['services', 'products', 'offerings'],
                    'features': ['features', 'key_features', 'core_features', 'functionality', 'capabilities'],
                    'goals': ['goals', 'key_goals', 'objectives'],
                    'style': ['style', 'design_style', 'visual_style', 'palette', 'color_palette', 'visual_direction'],
                    'tone': ['tone', 'voice', 'brand_voice', 'personality'],
                    'pages': ['pages', 'page_list', 'sitemap'],
                    'language': ['language', 'locale'],
                    'trip_types': ['trip_types', 'trip types', 'journeys'],
                    'passenger_types': ['passenger_types', 'passenger types'],
                    'addons': ['addons', 'add-ons', 'add ons'],
                    'payments': ['payments', 'payment_methods', 'payment methods'],
                    'policies': ['policies', 'policy', 'refund_policy', 'cancellation_policy']
                }
                normalized = {}
                for key, value in cleaned.items():
                    key_norm = key.strip().lower().replace('-', '_')
                    mapped = None
                    for target, aliases in alias_map.items():
                        if key_norm == target:
                            mapped = target
                            break
                        if key_norm in [a.replace(' ', '_') for a in aliases]:
                            mapped = target
                            break
                    normalized[mapped or key] = value
                cleaned = normalized
            return cleaned

        system_msg = "You suggest concise answer options for a website brief chat. Return JSON only."
        user_msg = (
            f"Prompt:\n{prompt}\n\n"
            f"Questions:\n{json.dumps(compact_questions)}\n\n"
            "Propose 3-5 improved options per question. Return JSON mapping question_id -> array of strings."
        )

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': config.ai_http_referer,
            'X-Title': config.ai_app_name
        }

        deadline = time.monotonic() + 10.0
        for model in models:
            if time.monotonic() > deadline:
                break
            try:
                payload = json.dumps({
                    'model': model,
                    'messages': [{'role': 'system', 'content': system_msg}, {'role': 'user', 'content': user_msg}],
                    'temperature': 0.1,
                    'max_tokens': 128
                }).encode('utf-8')
                req = urllib.request.Request(base_url, data=payload, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=5) as resp:
                    raw = resp.read().decode('utf-8')
                data = json.loads(raw)
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                cleaned = _parse_ai_json(content)
                if cleaned:
                    return _filter_options_by_context(cleaned)
            except urllib.error.HTTPError as e:
                self.last_ai_error = f"HTTP {e.code}: {e.reason}"
                if e.code == 402: continue # Try next model if credits out
            except Exception as e:
                self.last_ai_error = str(e)
                continue
        return {}

    def _ai_extract_brief(self, prompt: str) -> Dict[str, Any]:
        self.last_ai_error = None
        enabled = config.chat_ai_enabled
        if not enabled:
            return {}
        api_key = config.ai_api_key
        if not api_key:
            return {}

        base_url = config.chat_ai_base_url
        primary_model = config.chat_ai_model
        fallback_models = config.chat_ai_fallback_models
        models = []
        if primary_model:
            models.append(primary_model)
        for m in fallback_models:
            if m and m not in models:
                models.append(m)
        if not models:
            return {}

        system_msg = (
            "Extract a structured brief from a website prompt. Return JSON only."
        )
        user_msg = (
            "Rules:\n"
            "- Return a JSON object with keys: type, pages, services, features, goals, style, tone, language, showcase.\n"
            "- pages MUST be an array of page names.\n"
            "- For other fields, use a short string or an array if it is a list.\n"
            "- Only include information grounded in the prompt. If missing, use an empty string or empty array.\n"
            "- No markdown, no explanations.\n\n"
            f"Prompt:\n{prompt}"
        )

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': config.ai_http_referer,
            'X-Title': config.ai_app_name
        }

        deadline = time.monotonic() + 8.0

        for model in models:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return {}
            payload = json.dumps({
                'model': model,
                'messages': [
                    {'role': 'system', 'content': system_msg},
                    {'role': 'user', 'content': user_msg}
                ],
                'temperature': 0.1,
                'top_p': 0.9,
                'max_tokens': 96
            }).encode('utf-8')

            req = urllib.request.Request(
                base_url,
                data=payload,
                headers=headers,
                method='POST'
            )

            try:
                timeout = max(3, min(8, remaining))
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read().decode('utf-8')
                data = json.loads(raw)
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                content = self._strip_code_fences(content)
                if not content:
                    continue
                try:
                    parsed_json = json.loads(content)
                except json.JSONDecodeError:
                    start = content.find('{')
                    end = content.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        parsed_json = json.loads(content[start:end + 1])
                    else:
                        continue
                if not isinstance(parsed_json, dict):
                    continue
                cleaned: Dict[str, Any] = {}
                for key, value in parsed_json.items():
                    if key == 'pages':
                        if isinstance(value, list):
                            cleaned['pages'] = [str(v).strip() for v in value if str(v).strip()]
                        elif isinstance(value, str):
                            parts = [p.strip() for p in re.split(r'[,\|/;]| and ', value, flags=re.IGNORECASE) if p.strip()]
                            if parts:
                                cleaned['pages'] = parts
                        continue
                    if isinstance(value, list):
                        cleaned[key] = [str(v).strip() for v in value if str(v).strip()]
                        continue
                    if isinstance(value, str):
                        cleaned[key] = value.strip()
                if cleaned:
                    return cleaned
            except urllib.error.HTTPError as e:
                try:
                    body = e.read().decode('utf-8')
                except Exception:
                    body = ''
                self.last_ai_error = f"HTTP {e.code}: {body or e.reason}"
                continue
            except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as e:
                self.last_ai_error = str(e)
                continue
            except Exception:
                continue
        return {}

    def _merge_missing_fields(self, base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(base, dict):
            base = {}
        if not isinstance(incoming, dict):
            return base
        keys = [
            'client', 'type', 'pages', 'pages_text', 'pages_list', 'pages_tree',
            'services', 'features', 'goals', 'style', 'tone', 'language', 'showcase',
            'trip_types', 'passenger_types', 'addons', 'payments', 'policies'
        ]
        for key in keys:
            if not base.get(key) and incoming.get(key):
                base[key] = incoming.get(key)
        return base

    def _ai_generate_sections_map(self, prompt: str, normalized: Dict[str, Any], pages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Use AI to generate section lists for each page. Returns mapping page_name -> sections."""
        self.last_ai_error = None
        if not config.chat_ai_enabled:
            return {}
        api_key = config.ai_api_key
        if not api_key:
            return {}

        base_url = config.chat_ai_base_url
        primary_model = config.chat_ai_model
        fallback_models = config.chat_ai_fallback_models
        models = []
        if primary_model:
            models.append(primary_model)
        for m in fallback_models:
            if m and m not in models:
                models.append(m)
        if not models:
            return {}

        brief_context = {
            'type': normalized.get('type', ''),
            'pages': [p.get('name') for p in pages if p.get('name')],
            'services': normalized.get('services', ''),
            'features': normalized.get('features', ''),
            'goals': normalized.get('goals', ''),
            'style': normalized.get('style', ''),
            'tone': normalized.get('tone', ''),
            'language': normalized.get('language', ''),
            'showcase': normalized.get('showcase', '')
        }

        system_msg = "You generate concise, prompt-grounded website sections. Return JSON only."
        user_msg = (
            "Return a JSON object mapping each page name to an array of sections. "
            "Each section must be an object with keys: type, title, description. "
            "Use the prompt and brief context. No extra keys, no markdown, no explanations.\n\n"
            f"Prompt:\n{prompt}\n\n"
            f"Brief:\n{json.dumps(brief_context, ensure_ascii=True)}"
        )

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': config.ai_http_referer,
            'X-Title': config.ai_app_name
        }

        for model in models:
            payload = json.dumps({
                'model': model,
                'messages': [
                    {'role': 'system', 'content': system_msg},
                    {'role': 'user', 'content': user_msg}
                ],
                'temperature': 0.2,
                'top_p': 0.9,
                'max_tokens': 700
            }).encode('utf-8')

            req = urllib.request.Request(
                base_url,
                data=payload,
                headers=headers,
                method='POST'
            )

            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    raw = resp.read().decode('utf-8')
                data = json.loads(raw)
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                content = self._strip_code_fences(content)
                if not content:
                    continue
                parsed_json = json.loads(content)
                if not isinstance(parsed_json, dict):
                    continue
                cleaned: Dict[str, List[Dict[str, Any]]] = {}
                for page_name, sections in parsed_json.items():
                    if not isinstance(sections, list):
                        continue
                    cleaned_sections: List[Dict[str, Any]] = []
                    for s in sections:
                        if not isinstance(s, dict):
                            continue
                        title = str(s.get('title', '')).strip()
                        description = str(s.get('description', '')).strip()
                        type_ = str(s.get('type', '')).strip() or 'content'
                        if not title:
                            continue
                        cleaned_sections.append({
                            'type': type_,
                            'title': title,
                            'description': description
                        })
                    if cleaned_sections:
                        cleaned[page_name] = cleaned_sections
                if cleaned:
                    return cleaned
            except urllib.error.HTTPError as e:
                try:
                    body = e.read().decode('utf-8')
                except Exception:
                    body = ''
                self.last_ai_error = f"HTTP {e.code}: {body or e.reason}"
                continue
            except Exception as e:
                self.last_ai_error = str(e)
                continue
        return {}

    def _clean_page_name(self, name: str) -> str:
        cleaned = re.sub(r'\s+', ' ', name.strip())
        # Remove trailing "page" (but keep "dashboard")
        cleaned = re.sub(r'\s+page$', '', cleaned, flags=re.IGNORECASE)
        canonical_map = {
            'home': 'Home',
            'about us': 'About Us',
            'about': 'About',
            'service': 'Services',
            'services': 'Services',
            'contact': 'Contact',
            'login': 'Login',
            'register': 'Register',
            'signup': 'Register',
            'sign up': 'Register',
            'admin dashboard': 'Admin Dashboard',
            'user dashboard': 'User Dashboard',
            'agent dashboard': 'Agent Dashboard',
            'flights': 'Flights',
            'team registration': 'Team Registration',
            'fixtures': 'Fixtures',
            'live score': 'Live Scores',
            'live scores': 'Live Scores',
            'points table': 'Points Table',
            'standings': 'Standings',
            'player statistics': 'Player Statistics',
            'player stats': 'Player Statistics',
            'match results': 'Match Results',
            'match summaries': 'Match Summaries',
            'flight search': 'Flight Search',
            'flight listing': 'Flight Listing',
            'select flight': 'Select Flight',
            'checkout': 'Checkout',
            'passenger details': 'Passenger Details',
            'booking summary': 'Booking Summary',
            'booking summery': 'Booking Summary',
            'offers': 'Offers',
            'offer': 'Offers',
            'trending': 'Trending Movies',
            'trending movies': 'Trending Movies',
            'favorites': 'Favorites',
            'favourites': 'Favorites',
            'watchlist': 'Favorites',
            'one way trip': 'One Way Trip',
            'round trip': 'Round Trip',
            'gst details': 'GST Details',
            'terms & conditions': 'Terms & Conditions',
            'terms and condition': 'Terms & Conditions'
        }
        key = cleaned.lower()
        return canonical_map.get(key, cleaned).strip()

    def _dedupe_pages(self, pages: List[str]) -> List[str]:
        seen = set()
        result = []
        for page in pages:
            name = self._clean_page_name(str(page))
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(name)
        return result

    def _add_tree_path(self, tree: List[Dict[str, Any]], parts: List[str]) -> None:
        current = tree
        for part in parts:
            part = self._clean_page_name(part)
            if not part:
                continue
            existing = next((n for n in current if n['name'].lower() == part.lower()), None)
            if not existing:
                existing = {'name': part, 'children': []}
                current.append(existing)
            current = existing['children']

    def _merge_pages_into_tree(self, tree: List[Dict[str, Any]], pages: List[str]) -> List[Dict[str, Any]]:
        if not tree:
            tree = []

        def tree_contains_name(nodes: List[Dict[str, Any]], name: str) -> bool:
            for node in nodes:
                if node.get('name', '').lower() == name.lower():
                    return True
                if tree_contains_name(node.get('children', []), name):
                    return True
            return False

        for page in pages:
            name = self._clean_page_name(page)
            if not name:
                continue
            if '>' in name:
                parts = [p.strip() for p in name.split('>') if p.strip()]
                self._add_tree_path(tree, parts)
            else:
                if not tree_contains_name(tree, name):
                    tree.append({'name': name, 'children': []})
        return tree

    def _reorder_tree_by_pages(self, tree: List[Dict[str, Any]], pages: List[str]) -> List[Dict[str, Any]]:
        if not tree or not pages:
            return tree
        order_map = {self._clean_page_name(p).lower(): idx for idx, p in enumerate(pages) if p}

        def compute_index(node: Dict[str, Any]) -> Any:
            key = str(node.get('name', '')).lower()
            if key in order_map:
                return order_map[key]
            child_indices = []
            for child in node.get('children', []) or []:
                idx = compute_index(child)
                if idx is not None:
                    child_indices.append(idx)
            if child_indices:
                return min(child_indices)
            return None

        def reorder(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            for n in nodes:
                if n.get('children'):
                    n['children'] = reorder(n['children'])
            decorated = []
            for i, n in enumerate(nodes):
                idx = compute_index(n)
                decorated.append((idx if idx is not None else 10**9, i, n))
            decorated.sort(key=lambda x: (x[0], x[1]))
            return [d[2] for d in decorated]

        return reorder(tree)

    def _default_flight_booking_tree(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'Home', 'children': []},
            {'name': 'Flights', 'children': [
                {'name': 'Flight Search', 'children': []},
                {'name': 'Flight Listing', 'children': []},
                {'name': 'Select Flight', 'children': []},
                {'name': 'Passenger Details', 'children': []},
                {'name': 'Add-ons', 'children': []},
                {'name': 'Checkout', 'children': []},
                {'name': 'Booking Summary', 'children': []},
                {'name': 'GST Details', 'children': []},
                {'name': 'Terms & Conditions', 'children': []}
            ]},
            {'name': 'Offers', 'children': []},
            {'name': 'About Us', 'children': []},
            {'name': 'Services', 'children': []},
            {'name': 'Contact', 'children': []},
            {'name': 'Login', 'children': []},
            {'name': 'Register', 'children': []},
            {'name': 'Admin Dashboard', 'children': []},
            {'name': 'User Dashboard', 'children': []},
            {'name': 'Agent Dashboard', 'children': []}
        ]

    def _extract_page_candidates_from_text(self, text: str) -> List[str]:
        if not text:
            return []

        stopwords = {
            'and', 'or', 'the', 'a', 'an', 'to', 'for', 'of', 'in', 'on', 'with',
            'by', 'your', 'our', 'is', 'are', 'be', 'should', 'get', 'add', 'select',
            'then', 'next', 'from', 'at', 'as', 'this', 'that', 'it', 'me', 'my',
            'ours', 'we', 'i', 'please', 'website', 'site', 'login', 'register'
        }
        candidates = []

        lower = text.lower()
        keyword_pages = [
            ('home page', 'Home'),
            ('home', 'Home'),
            ('recipe search', 'Recipe Search'),
            ('recipes search', 'Recipe Search'),
            ('recipe', 'Recipes'),
            ('recipes', 'Recipes'),
            ('categories', 'Categories'),
            ('favorites', 'Favorites'),
            ('courses', 'Courses'),
            ('course listings', 'Courses'),
            ('course listing', 'Courses'),
            ('course', 'Courses'),
            ('instructors', 'Instructors'),
            ('instructor profiles', 'Instructors'),
            ('instructor', 'Instructors'),
            ('student reviews', 'Student Reviews'),
            ('student review', 'Student Reviews'),
            ('testimonials', 'Testimonials'),
            ('testimonial', 'Testimonials'),
            ('enrollment', 'Enrollment'),
            ('enroll', 'Enrollment'),
            ('flights', 'Flights'),
            ('team registration', 'Team Registration'),
            ('fixtures', 'Fixtures'),
            ('live score', 'Live Scores'),
            ('live scores', 'Live Scores'),
            ('points table', 'Points Table'),
            ('standings', 'Standings'),
            ('player statistics', 'Player Statistics'),
            ('player stats', 'Player Statistics'),
            ('match results', 'Match Results'),
            ('match summaries', 'Match Summaries'),
            ('about us', 'About Us'),
            ('about', 'About'),
            ('service', 'Services'),
            ('services', 'Services'),
            ('contact', 'Contact'),
            ('login', 'Login'),
            ('register', 'Register'),
            ('signup', 'Register'),
            ('sign up', 'Register'),
            ('admin dashboard', 'Admin Dashboard'),
            ('user dashboard', 'User Dashboard'),
            ('agent dashboard', 'Agent Dashboard'),
            ('one way trip', 'One Way Trip'),
            ('one-way trip', 'One Way Trip'),
            ('one way', 'One Way Trip'),
            ('round trip', 'Round Trip'),
            ('passenger details', 'Passenger Details'),
            ('flight search', 'Flight Search'),
            ('flight listing', 'Flight Listing'),
            ('fligh listing', 'Flight Listing'),
            ('select flight', 'Select Flight'),
            ('checkout', 'Checkout'),
            ('add-ons', 'Add-ons'),
            ('addons', 'Add-ons'),
            ('add-on', 'Add-ons'),
            ("addon's", 'Add-ons'),
            ('booking summary', 'Booking Summary'),
            ('booking summery', 'Booking Summary'),
            ('gst', 'GST Details'),
            ('terms and condition', 'Terms & Conditions'),
            ('terms & conditions', 'Terms & Conditions'),
            ('terms', 'Terms & Conditions'),
            ("offer's", 'Offers'),
            ('offers', 'Offers'),
            ('offer', 'Offers')
        ]
        # Preserve order by scanning text left-to-right
        positions = []
        for key, label in keyword_pages:
            idx = lower.find(key)
            if idx != -1:
                positions.append((idx, label))
        positions.sort(key=lambda x: x[0])
        for _, label in positions:
            candidates.append(label)

        return self._dedupe_pages(candidates)

    def parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """Parse a freeform prompt into a structured brief."""
        text = (prompt or "").strip()
        if not text:
            return {}

        raw_lines = [line for line in re.split(r'[\r\n]+', text)]
        lines = [line.strip() for line in raw_lines if line.strip()]
        normalized_text = re.sub(r'[\r\n]+', ' ', text)

        def find_labeled_value(patterns: List[str]) -> str:
            for line in lines:
                for pat in patterns:
                    m = re.match(pat, line, flags=re.IGNORECASE)
                    if m:
                        return m.group(1).strip()
            for pat in patterns:
                m = re.search(pat, normalized_text, flags=re.IGNORECASE)
                if m:
                    return m.group(1).strip()
            return ""

        def split_list(value: str) -> List[str]:
            if not value:
                return []
            cleaned = value.strip()
            if re.fullmatch(r'\d+\s*(?:pages?)?', cleaned, flags=re.IGNORECASE):
                return []
            cleaned = re.sub(r'[.!?]+$', '', cleaned)
            cleaned = re.sub(r'[\[\]\(\)]', '', cleaned)
            cleaned = re.sub(r'[\r\n]+', ',', cleaned)
            cleaned = cleaned.replace(';', ',').replace('|', ',').replace('/', ',')
            cleaned = cleaned.replace('&', ',')
            cleaned = re.sub(r'\band\b', ',', cleaned, flags=re.IGNORECASE)
            parts = [p.strip() for p in cleaned.split(',') if p.strip()]
            # Filter out obviously non-page tokens
            filtered = []
            for p in parts:
                if re.fullmatch(r'\d+\s*(?:pages?)?', p, flags=re.IGNORECASE):
                    continue
                if len(p) <= 1:
                    continue
                filtered.append(p)
            return filtered

        def extract_bulleted_block(start_index: int) -> List[str]:
            block = []
            for i in range(start_index + 1, len(raw_lines)):
                line = raw_lines[i]
                if not line.strip():
                    break
                if re.match(r'^\s*(?:[-*•]|\d+[\.\)])\s+', line):
                    block.append(line)
                    continue
                # Stop if another labeled field begins
                if re.match(r'^\s*\w[\w\s]+\s*[:\-]\s*.+$', line):
                    break
                break
            return block

        def parse_page_tree_from_bullets(list_lines: List[str]) -> List[Dict[str, Any]]:
            tree: List[Dict[str, Any]] = []
            stack: List[Dict[str, Any]] = []
            indent_stack: List[int] = []
            for raw in list_lines:
                if not re.match(r'^\s*(?:[-*•]|\d+[\.\)])\s+', raw):
                    continue
                indent = len(raw) - len(raw.lstrip(' '))
                name = re.sub(r'^\s*(?:[-*•]|\d+[\.\)])\s+', '', raw).strip()
                if not name:
                    continue
                node = {'name': name, 'children': []}
                while indent_stack and indent <= indent_stack[-1]:
                    indent_stack.pop()
                    stack.pop()
                if stack:
                    stack[-1]['children'].append(node)
                else:
                    tree.append(node)
                stack.append(node)
                indent_stack.append(indent)
            return tree

        def add_tree_path(tree: List[Dict[str, Any]], parts: List[str]) -> None:
            current = tree
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                existing = next((n for n in current if n['name'].lower() == part.lower()), None)
                if not existing:
                    existing = {'name': part, 'children': []}
                    current.append(existing)
                current = existing['children']

        def parse_page_tree_from_paths(value: str) -> List[Dict[str, Any]]:
            tree: List[Dict[str, Any]] = []
            if not value:
                return tree
            paths = [p.strip() for p in re.split(r'[;\n]+', value) if p.strip()]
            for path in paths:
                if '>' in path:
                    parts = [p.strip() for p in path.split('>') if p.strip()]
                    add_tree_path(tree, parts)
                else:
                    parts = [p.strip() for p in re.split(r'[,\|/]| and ', path, flags=re.IGNORECASE) if p.strip()]
                    for part in parts:
                        add_tree_path(tree, [part])
            return tree

        data: Dict[str, Any] = {}

        # JSON-like prompt block support
        json_data = None
        if '{' in text and '}' in text:
            try:
                json_text = text[text.index('{'):text.rindex('}') + 1]
                json_data = json.loads(json_text)
            except Exception:
                json_data = None

        if isinstance(json_data, dict):
            key_map = {
                'client': 'client',
                'company': 'client',
                'brand': 'client',
                'title': 'client',
                'site_name': 'client',
                'type': 'type',
                'website_type': 'type',
                'pages': 'pages',
                'sitemap': 'pages',
                'services': 'services',
                'features': 'features',
                'goals': 'goals',
                'style': 'style',
                'tone': 'tone',
                'language': 'language',
                'showcase': 'showcase'
            }
            for key, target in key_map.items():
                if key in json_data and json_data[key]:
                    data[target] = json_data[key]
            pages_val = json_data.get('pages') or json_data.get('sitemap')
            if isinstance(pages_val, list) and pages_val and isinstance(pages_val[0], dict) and 'children' in pages_val[0]:
                data['pages_tree'] = pages_val

        # Labeled fields
        data['client'] = find_labeled_value([
            r'^(?:client|company|brand|business|site name|site title|title)\s*[:\-]\s*(.+)$'
        ])
        data['type'] = find_labeled_value([
            r'^(?:type|website type|site type|project type|website)\s*[:\-]\s*(.+)$'
        ])
        pages_text = find_labeled_value([
            r'^(?:pages?|page list|sitemap|include pages|pages include)\s*[:\-]\s*(.+)$'
        ])
        if not pages_text:
            inline_pages_patterns = [
                r'(?:pages?|page list|sitemap)\s*(?:include|includes|including|are|is|should include|to include)?\s*[:\-]\s*([^.\n]+)',
                r'(?:pages?|page list|sitemap)\s*(?:include|including|should include|to include)\s+([^.\n]+)',
                r'(?:include|including)\s+pages?\s*[:\-]\s*([^.\n]+)'
            ]
            for pat in inline_pages_patterns:
                inline_pages_match = re.search(pat, normalized_text, flags=re.IGNORECASE)
                if inline_pages_match:
                    pages_text = inline_pages_match.group(1).strip()
                    break
        services_text = find_labeled_value([
            r'^(?:services?|offerings?|products?)\s*[:\-]\s*(.+)$'
        ])
        addons_text = find_labeled_value([
            r'^(?:addons?|add-ons?|ancillary|extras)\s*[:\-]\s*(.+)$'
        ])
        features_text = find_labeled_value([
            r'^(?:features?|functionality|capabilities)\s*[:\-]\s*(.+)$'
        ])
        goals_text = find_labeled_value([
            r'^(?:goals?|objectives?|purpose|primary goal|project goals?)\s*[:\-]\s*(.+)$'
        ])
        style_text = find_labeled_value([
            r'^(?:style|design style|visual style|color palette|visual direction)\s*[:\-]\s*(.+)$'
        ])
        tone_text = find_labeled_value([
            r'^(?:tone|brand tone|brand personality|voice)\s*[:\-]\s*(.+)$'
        ])
        payments_text = find_labeled_value([
            r'^(?:payments?|payment methods?)\s*[:\-]\s*(.+)$'
        ])
        policies_text = find_labeled_value([
            r'^(?:policies?|refunds?|cancellation|terms)\s*[:\-]\s*(.+)$'
        ])
        passenger_text = find_labeled_value([
            r'^(?:passengers?|passenger types?)\s*[:\-]\s*(.+)$'
        ])
        trip_text = find_labeled_value([
            r'^(?:trip types?|journey types?)\s*[:\-]\s*(.+)$'
        ])
        language_text = find_labeled_value([
            r'^(?:language|site language|locale)\s*[:\-]\s*(.+)$'
        ])
        showcase_text = find_labeled_value([
            r'^(?:showcase|primary function|primary focus|main focus|focus)\s*[:\-]\s*(.+)$'
        ])

        pages_tree = []
        explicit_pages = False
        for idx, raw in enumerate(raw_lines):
            if re.match(r'^\s*(?:pages?|page list|sitemap)\s*[:\-]\s*.*$', raw, flags=re.IGNORECASE):
                bullet_block = extract_bulleted_block(idx)
                if bullet_block:
                    pages_tree = parse_page_tree_from_bullets(bullet_block)
                break

        if pages_text:
            page_list = self._dedupe_pages(split_list(pages_text))
            data['pages'] = page_list
            data['pages_text'] = ', '.join(page_list) if page_list else pages_text
            if '>' in pages_text:
                pages_tree = parse_page_tree_from_paths(pages_text)
            explicit_pages = True
        if services_text:
            data['services'] = services_text
        if addons_text:
            data['addons'] = addons_text
        if features_text:
            data['features'] = features_text
        if goals_text:
            data['goals'] = goals_text
        if style_text:
            data['style'] = style_text
        if tone_text:
            data['tone'] = tone_text
        if payments_text:
            data['payments'] = payments_text
        if policies_text:
            data['policies'] = policies_text
        if passenger_text:
            data['passenger_types'] = passenger_text
        if trip_text:
            data['trip_types'] = trip_text
        if language_text:
            data['language'] = language_text
        if showcase_text:
            data['showcase'] = showcase_text

        # Extract feature-like lists from natural language
        if not data.get('features') or not data.get('services'):
            def extract_list_after(phrases: List[str]) -> List[str]:
                found: List[str] = []
                for phrase in phrases:
                    for m in re.finditer(phrase, text, flags=re.IGNORECASE):
                        segment = (m.group(1) or '').strip()
                        if segment:
                            if re.match(r'^(?:pages?|page list|sitemap)\b', segment, flags=re.IGNORECASE):
                                continue
                            found.extend(split_list(segment))
                return found

            feature_phrases = [
                r'\bincludes?\s+([^.\n]+)',
                r'\bincluding\s+([^.\n]+)',
                r'\bshould\s+include\s+([^.\n]+)',
                r'\bshould\s+have\s+([^.\n]+)',
                r'\bshould\s+highlight\s+([^.\n]+)',
                r'\bhighlight(?:s|ing)?\s+([^.\n]+)',
                r'\bfeaturing\s+([^.\n]+)',
                r'\balong\s+with\s+([^.\n]+)',
                r'\bwith\s+(?:a\s+)?focus\s+on\s+([^.\n]+)',
                r'\bfocus(?:ed)?\s+on\s+([^.\n]+)',
                r'\ballow(?:s)?\s+(?:users?|admins?|administrators?)\s+to\s+([^.\n]+)',
                r'\busers?\s+can\s+([^.\n]+)'
            ]
            extracted_features = extract_list_after(feature_phrases)
            if extracted_features:
                deduped = self._dedupe_pages(extracted_features)
                if not data.get('features'):
                    data['features'] = ', '.join(deduped)
                if not data.get('services') and len(deduped) <= 8:
                    if re.search(r'\bservices?\b|\bofferings?\b|\bwe provide\b|\bwe offer\b', text, re.IGNORECASE):
                        data['services'] = ', '.join(deduped)

        # Infer services/products from "store/shop for X products"
        if not data.get('services'):
            m = re.search(r'\b(?:store|shop)\s+for\s+([^.\n]+?)\s+products?\b', text, re.IGNORECASE)
            if m:
                prod = m.group(1).strip()
                if prod:
                    data['services'] = f"{prod} products"

        # Infer goals from focus/experience language
        if not data.get('goals'):
            goal_phrases = [
                r'\bwith\s+(?:a\s+)?focus\s+on\s+([^.\n]+)',
                r'\bfocus(?:ed)?\s+on\s+([^.\n]+)',
                r'\bto\s+create\s+([^.\n]+)',
                r'\bto\s+provide\s+([^.\n]+)',
                r'\bto\s+deliver\s+([^.\n]+)'
            ]
            extracted_goals = extract_list_after(goal_phrases)
            if extracted_goals:
                deduped_goals = self._dedupe_pages(extracted_goals)
                if deduped_goals:
                    data['goals'] = ', '.join(deduped_goals)

        # Infer design style if explicitly mentioned
        if not data.get('style'):
            style_terms = []
            if re.search(r'\bresponsive\b', text, re.IGNORECASE):
                style_terms.append('Responsive')
            if re.search(r'\bmodern\b', text, re.IGNORECASE):
                style_terms.append('Modern')
            if re.search(r'\bclean\b', text, re.IGNORECASE):
                style_terms.append('Clean')
            if re.search(r'\bminimal(ist)?\b', text, re.IGNORECASE):
                style_terms.append('Minimal')
            if style_terms:
                data['style'] = ', '.join(dict.fromkeys(style_terms))

        if pages_tree:
            data['pages_tree'] = pages_tree
            if isinstance(data.get('pages'), list) and data['pages'] and isinstance(data['pages'][0], dict):
                data.pop('pages', None)
            explicit_pages = True

        # Intent-based hints
        intent = self._detect_intent(text)
        if not data.get('type') and intent.get('type'):
            data['type'] = intent['type']
        if not data.get('type'):
            if re.search(r'\bflight\b', text, re.IGNORECASE) or re.search(r'\bflight booking\b', text, re.IGNORECASE):
                data['type'] = 'Flight Booking Website'

        if intent.get('type') == 'Flight Booking Website':
            if not data.get('pages'):
                extracted_pages = self._extract_page_candidates_from_text(text)
                if extracted_pages:
                    data['pages'] = extracted_pages
                    data['pages_text'] = ', '.join(extracted_pages)
            auto_filled = []
            if not data.get('features'):
                data['features'] = 'Fare calendar, Seat selection, Meal add-ons, Baggage add-ons, PNR status, Refund & cancellation, Coupons, GST invoice'
                auto_filled.append('features')
            if not data.get('services'):
                data['services'] = 'Domestic flights, One-way trips, Round trips, Group bookings, Agent bookings'
                auto_filled.append('services')
            if not data.get('addons'):
                data['addons'] = 'Extra baggage, Seat selection, Meals, Travel insurance, Priority boarding'
                auto_filled.append('addons')
            if not data.get('payments'):
                data['payments'] = 'UPI, Credit/Debit Cards, Net Banking, Wallets'
                auto_filled.append('payments')
            if not data.get('policies'):
                data['policies'] = 'Cancellation rules, Refund policy, No-show policy, Change fees'
                auto_filled.append('policies')
            if not data.get('trip_types'):
                data['trip_types'] = 'One-way, Round trip, Multi-city'
                auto_filled.append('trip_types')
            if not data.get('passenger_types'):
                data['passenger_types'] = 'Adult, Child, Infant'
                auto_filled.append('passenger_types')
            if not data.get('pages_tree'):
                data['pages_tree'] = self._default_flight_booking_tree()
            if data.get('pages'):
                pages_list = data['pages'] if isinstance(data['pages'], list) else split_list(str(data['pages']))
                if pages_list:
                    # Ensure Flights parent appears before flight-specific subpages
                    if not any(p.lower() == 'flights' for p in pages_list):
                        flight_children = {'flight search', 'flight listing', 'select flight', 'passenger details', 'add-ons', 'checkout', 'booking summary', 'gst details', 'terms & conditions'}
                        insert_at = None
                        for idx, p in enumerate(pages_list):
                            if p.lower() in flight_children:
                                insert_at = idx
                                break
                        if insert_at is None:
                            pages_list.insert(1 if pages_list and pages_list[0].lower() == 'home' else 0, 'Flights')
                        else:
                            pages_list.insert(insert_at, 'Flights')
                    data['pages_tree'] = self._merge_pages_into_tree(data['pages_tree'], pages_list)
                    data['pages'] = self._dedupe_pages(pages_list)
                    data['pages_tree'] = self._reorder_tree_by_pages(data['pages_tree'], data['pages'])
                    data['pages_text'] = ', '.join(data['pages'])
            if auto_filled:
                data['auto_filled'] = auto_filled

        # Infer Business Type from prompt if still missing
        if not data.get('type'):
            type_match = re.search(
                r'\b(?:build|create|design|develop|make)\s+(?:an?|the)?\s*([a-z0-9][a-z0-9\s&\-\+]{0,40}?)\s+(website|web site|site|platform|app|application|system)\b',
                text,
                flags=re.IGNORECASE
            )
            if not type_match:
                type_match = re.search(
                    r'\b([a-z0-9][a-z0-9\s&\-\+]{0,40}?)\s+(website|web site|site|platform|app|application|system)\b',
                    text,
                    flags=re.IGNORECASE
                )
            if type_match:
                raw_label = type_match.group(1).strip()
                raw_label = re.sub(r'^(?:build|create|design|develop|make|generate)\s+', '', raw_label, flags=re.IGNORECASE)
                raw_label = re.sub(r'^(?:a|an|the)\s+', '', raw_label, flags=re.IGNORECASE)
                raw_label = re.sub(r'\s+for\s+me$', '', raw_label, flags=re.IGNORECASE).strip()
                label = ' '.join(word.capitalize() for word in raw_label.split())
                suffix = type_match.group(2).lower()
                if 'app' in suffix or 'application' in suffix:
                    data['type'] = f"{label} App"
                elif 'platform' in suffix:
                    data['type'] = f"{label} Platform"
                elif 'system' in suffix:
                    data['type'] = f"{label} System"
                else:
                    data['type'] = f"{label} Website"

        # Ensure Business Type is always present
        if not data.get('type'):
            data['type'] = 'Business Website'

        # Infer language if mentioned
        if not data.get('language'):
            lang_match = re.search(r'\b(english|spanish|french|german|hindi|arabic)\b', text, re.IGNORECASE)
            if lang_match:
                data['language'] = lang_match.group(1).capitalize()
        if not data.get('language'):
            data['language'] = 'English'

        # AI extraction fallback for missing fields
        missing_keys = [k for k in ['type', 'pages', 'services', 'features', 'goals', 'style', 'tone', 'language', 'showcase'] if not data.get(k)]
        if missing_keys or (not explicit_pages and (not data.get('pages') or len(data.get('pages', [])) < 2)):
            ai_brief = self._ai_extract_brief(text)
            if isinstance(ai_brief, dict) and ai_brief:
                if not data.get('type') and ai_brief.get('type'):
                    data['type'] = ai_brief.get('type')
                if not explicit_pages and not data.get('pages') and ai_brief.get('pages'):
                    pages_list = ai_brief.get('pages')
                    if isinstance(pages_list, list):
                        data['pages'] = self._dedupe_pages(pages_list)
                        data['pages_text'] = ', '.join(data['pages'])
                for key in ['services', 'features', 'goals', 'style', 'tone', 'language', 'showcase']:
                    if not data.get(key) and ai_brief.get(key):
                        data[key] = ai_brief.get(key)

        # Try to detect page list even without labels
        if not explicit_pages and not data.get('pages') and not data.get('pages_tree'):
            unlabeled_pages = self._extract_mentioned_pages(text.lower())
            if unlabeled_pages:
                pages_deduped = self._dedupe_pages(unlabeled_pages)
                # Only accept inferred pages if it looks like a page list (avoid false hits like "at home")
                if len(pages_deduped) >= 3 or re.search(r'\bpages?\b', text, re.IGNORECASE):
                    data['pages'] = pages_deduped
                    data['pages_text'] = ', '.join(pages_deduped)

        if not explicit_pages and not data.get('pages_tree'):
            extracted_pages = self._extract_page_candidates_from_text(text)
            if extracted_pages:
                if len(extracted_pages) < 3 and not re.search(r'\bpages?\b', text, re.IGNORECASE):
                    extracted_pages = []
                if data.get('pages'):
                    existing = [self._clean_page_name(p) for p in data['pages']]
                    existing_map = {p.lower(): p for p in existing if p}
                    combined = []
                    seen = set()
                    # Preserve existing order first, then append any new extracted pages
                    for p in existing:
                        key = p.lower()
                        if key in seen:
                            continue
                        seen.add(key)
                        combined.append(existing_map.get(key, p))
                    for p in extracted_pages:
                        key = p.lower()
                        if key in seen:
                            continue
                        seen.add(key)
                        combined.append(p)
                    data['pages'] = combined
                    data['pages_text'] = ', '.join(combined)
                else:
                    if extracted_pages:
                        data['pages'] = extracted_pages
                        data['pages_text'] = ', '.join(extracted_pages)

        if not explicit_pages and not data.get('pages') and not data.get('pages_tree') and intent.get('pages'):
            data['pages'] = intent['pages']
            data['pages_text'] = ', '.join(intent['pages'])

        # Page count (e.g., "5 pages")
        count_match = re.search(r'(\d+)\s*(?:page|pages)\b', text, re.IGNORECASE)
        if count_match:
            data['page_count'] = min(int(count_match.group(1)), 20)

        travel_fields = []
        if intent.get('type') == 'Flight Booking Website':
            travel_fields = ['trip_types', 'passenger_types', 'addons', 'payments', 'policies']

        expected_fields = ['client', 'type', 'pages', 'services', 'features', 'goals', 'style', 'tone', 'language', 'showcase'] + travel_fields
        auto_filled = set(data.get('auto_filled', [])) if isinstance(data.get('auto_filled'), list) else set()
        present = set()
        for key in expected_fields:
            if key == 'pages':
                if data.get('pages') or data.get('pages_tree'):
                    present.add('pages')
            elif data.get(key) and key not in auto_filled:
                present.add(key)
        missing = [k for k in expected_fields if k not in present]
        if expected_fields:
            data['confidence'] = round(len(present) / len(expected_fields), 2)
        data['missing_fields'] = missing

        return {k: v for k, v in data.items() if v}

    def _normalize_brief(self, prompt: str, brief_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Merge parsed prompt data with brief_data (brief_data wins)."""
        normalized = self.parse_prompt(prompt)

        if isinstance(brief_data, dict):
            for key in ['client', 'type', 'pages', 'services', 'features', 'goals', 'style', 'tone', 'language', 'showcase', 'sitemap', 'pages_tree', 'trip_types', 'passenger_types', 'addons', 'payments', 'policies']:
                val = brief_data.get(key)
                if key == 'pages_tree' and isinstance(val, list):
                    normalized['pages_tree'] = val
                    continue
                if key == 'pages' and isinstance(val, list) and val and isinstance(val[0], dict):
                    normalized['pages_tree'] = val
                    continue
                if isinstance(val, list):
                    val = ', '.join([str(v).strip() for v in val if str(v).strip()])
                if val:
                    # Allow sitemap -> pages mapping
                    if key == 'sitemap' and not brief_data.get('pages'):
                        normalized['pages'] = val
                    else:
                        normalized[key] = val

        # Normalize pages into list + text
        pages_value = normalized.get('pages')
        if isinstance(pages_value, list):
            pages_list = pages_value
        else:
            pages_list = []
            if isinstance(pages_value, str) and pages_value.strip():
                pages_list = [p.strip() for p in re.split(r'[,\|/]| and ', pages_value, flags=re.IGNORECASE) if p.strip()]

        if pages_list:
            normalized['pages_list'] = pages_list
            normalized['pages_text'] = ', '.join(pages_list)

        return normalized

    def _build_sections_for_page(self, page_name_lower: str, normalized: Dict[str, Any]) -> List[Dict[str, Any]]:
        sections: List[Dict[str, Any]] = []
        services = normalized.get('services', '')
        features = normalized.get('features', '')
        goals = normalized.get('goals', '')
        client_name = normalized.get('client', 'our site')
        showcase_goal = normalized.get('showcase', '')
        addons = normalized.get('addons', '')
        payments = normalized.get('payments', '')
        policies = normalized.get('policies', '')
        trip_types = normalized.get('trip_types', '')
        passenger_types = normalized.get('passenger_types', '')
        website_type = normalized.get('type', '')
        prompt_text = (normalized.get('prompt_text') or '').lower()

        def _limit(items: List[Dict[str, Any]], min_count: int = 5, max_count: int = 8) -> List[Dict[str, Any]]:
            if len(items) <= max_count:
                return items
            return items[:max_count]

        def _summary(*vals: Any) -> str:
            for v in vals:
                if not v:
                    continue
                if isinstance(v, list):
                    v = ', '.join([str(x).strip() for x in v if str(x).strip()])
                v = str(v).strip()
                if v:
                    return v
            return ''

        def _add(type_: str, title: str, description: str) -> None:
            sections.append({'type': type_, 'title': title, 'description': description})

        def _base(title: str, subtitle: str = '') -> None:
            _add('navbar', 'Navbar', 'Main navigation')
            desc = subtitle or _summary(showcase_goal, goals, features)
            _add('hero', title, desc or f'Overview of {client_name}')

        if 'home' in page_name_lower:
            _base('Home Hero', f'Welcome to {client_name}. {_summary(showcase_goal, goals)}'.strip())
            if services:
                _add('services', 'Our Services', f'We offer: {services}')
            if features:
                _add('features', 'Key Features', f'Special features: {features}')
            if website_type.lower().startswith('flight booking'):
                if trip_types:
                    _add('trip-types', 'Trip Types', f'Supported trips: {trip_types}')
                _add('offers', 'Top Offers', 'Highlighted fare deals and seasonal promotions')
                _add('trust', 'Why Book With Us', 'Trust badges, secure payments, airline partners, and customer support')
            _add('footer', 'Footer', 'Site footer')

        elif 'flight search' in page_name_lower:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'search-form', 'title': 'Search Form', 'description': 'From/To, dates, passengers, cabin class, and trip type selection'},
                {'type': 'filters', 'title': 'Quick Filters', 'description': 'Non-stop, time of day, airlines, price range'},
                {'type': 'promo', 'title': 'Promo Banner', 'description': 'Coupons or special fare banner'},
                {'type': 'footer', 'title': 'Footer', 'description': 'Site footer'}
            ]

        elif page_name_lower == 'flights':
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'search-form', 'title': 'Search Flights', 'description': 'Start a new search quickly'},
                {'type': 'highlights', 'title': 'Popular Routes', 'description': 'Top destinations and popular routes'},
                {'type': 'offers', 'title': 'Flight Offers', 'description': 'Trending deals and promotions'},
                {'type': 'footer', 'title': 'Footer', 'description': 'Site footer'}
            ]

        elif 'flight listing' in page_name_lower:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'results', 'title': 'Flight Results', 'description': 'List of available flights with fare, duration, stops'},
                {'type': 'sorting', 'title': 'Sort & Compare', 'description': 'Sort by price, duration, departure time; compare airlines'},
                {'type': 'filters', 'title': 'Advanced Filters', 'description': 'Stops, layover duration, refundable, baggage'},
                {'type': 'footer', 'title': 'Footer', 'description': 'Site footer'}
            ]

        elif 'select flight' in page_name_lower:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'fare-details', 'title': 'Fare Details', 'description': 'Fare rules, baggage allowance, cancellation terms'},
                {'type': 'seat-selection', 'title': 'Seat Selection', 'description': 'Seat map with pricing tiers and availability'},
                {'type': 'cta', 'title': 'Continue', 'description': 'Proceed to passenger details'}
            ]

        elif 'passenger details' in page_name_lower:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'passenger-form', 'title': 'Passenger Details', 'description': f'Name, DOB, gender, ID info; types: {passenger_types or "Adult/Child/Infant"}'},
                {'type': 'contact', 'title': 'Contact Details', 'description': 'Email and phone for booking updates'},
                {'type': 'special-requests', 'title': 'Special Requests', 'description': 'Meal preference, assistance requests'},
                {'type': 'cta', 'title': 'Continue', 'description': 'Proceed to add-ons or checkout'}
            ]

        elif 'add-on' in page_name_lower or 'add ons' in page_name_lower or 'addons' in page_name_lower:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'addons', 'title': 'Select Add-ons', 'description': f'Optional extras: {addons or "Baggage, Seats, Meals, Insurance"}'},
                {'type': 'pricing', 'title': 'Add-on Pricing', 'description': 'Price breakdown per add-on'},
                {'type': 'cta', 'title': 'Continue', 'description': 'Proceed to checkout'}
            ]

        elif 'checkout' in page_name_lower:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'order-summary', 'title': 'Booking Summary', 'description': 'Base fare, taxes, add-ons, discounts'},
                {'type': 'gst', 'title': 'GST Details', 'description': 'GST number, company info, tax invoice'},
                {'type': 'payment', 'title': 'Payment', 'description': f'Payment methods: {payments or "UPI, Cards, Net Banking"}'},
                {'type': 'terms', 'title': 'Terms & Conditions', 'description': 'Accept terms checkbox'},
                {'type': 'cta', 'title': 'Pay Now', 'description': 'Complete booking'}
            ]

        elif 'booking summary' in page_name_lower:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'summary', 'title': 'Booking Summary', 'description': 'Final itinerary, passengers, fare, add-ons'},
                {'type': 'gst', 'title': 'GST Breakdown', 'description': 'GST subtotal and invoice details'},
                {'type': 'cta', 'title': 'Download Ticket', 'description': 'Download or email e-ticket'}
            ]

        elif 'gst' in page_name_lower:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'gst-form', 'title': 'GST Details', 'description': 'Business name, GSTIN, address'},
                {'type': 'invoice', 'title': 'Invoice Preview', 'description': 'GST invoice preview before payment'}
            ]

        elif 'terms' in page_name_lower:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'policies', 'title': 'Policies', 'description': policies or 'Cancellation, refund, and no-show policies'},
                {'type': 'legal', 'title': 'Terms & Conditions', 'description': 'Booking rules and legal terms'}
            ]

        elif 'offer' in page_name_lower:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'offers', 'title': 'Offers & Coupons', 'description': 'Active deals, promo codes, bank offers'},
                {'type': 'cta', 'title': 'Book Now', 'description': 'Apply offer and continue booking'}
            ]

        elif 'login' in page_name_lower:
            sections = [
                {'type': 'auth', 'title': 'Login', 'description': 'Email/phone login with OTP or password'},
                {'type': 'help', 'title': 'Help & Support', 'description': 'Account recovery and assistance'}
            ]

        elif 'register' in page_name_lower or 'signup' in page_name_lower:
            sections = [
                {'type': 'auth', 'title': 'Create Account', 'description': 'Name, email/phone, OTP verification'},
                {'type': 'benefits', 'title': 'Member Benefits', 'description': 'Faster checkout, saved passengers, offers'}
            ]

        elif 'dashboard' in page_name_lower:
            role = 'User'
            if 'admin' in page_name_lower:
                role = 'Admin'
            elif 'agent' in page_name_lower:
                role = 'Agent'
            sections = [
                {'type': 'navbar', 'title': f'{role} Dashboard', 'description': f'{role} overview and quick actions'},
                {'type': 'stats', 'title': 'Key Metrics', 'description': 'Bookings, revenue, cancellations, active users'},
                {'type': 'management', 'title': 'Manage Bookings', 'description': 'Search, modify, cancel, issue refunds'},
                {'type': 'support', 'title': 'Support Tickets', 'description': 'Customer support queue and status'}
            ]

        elif 'about' in page_name_lower:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'hero', 'title': 'About Us', 'description': f'About {client_name} and our mission'},
                {'type': 'story', 'title': 'Our Story', 'description': 'Company background and milestones'},
                {'type': 'trust', 'title': 'Trust & Safety', 'description': 'Security, partnerships, compliance'},
                {'type': 'footer', 'title': 'Footer', 'description': 'Site footer'}
            ]

        elif 'service' in page_name_lower and services:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'hero', 'title': 'Our Services', 'description': f'Professional services offered by {client_name}'},
                {'type': 'content', 'title': 'Service Details', 'description': f'We provide the following services: {services}'},
                {'type': 'footer', 'title': 'Footer', 'description': 'Site footer'}
            ]

        elif 'contact' in page_name_lower:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'contact', 'title': 'Contact Us', 'description': 'Contact form and support channels'},
                {'type': 'support', 'title': 'Support', 'description': '24x7 support email/phone and FAQ'},
                {'type': 'footer', 'title': 'Footer', 'description': 'Site footer'}
            ]

        elif 'feature' in page_name_lower and features:
            sections = [
                {'type': 'navbar', 'title': 'Navbar', 'description': 'Main navigation'},
                {'type': 'hero', 'title': 'Platform Features', 'description': f'Core capabilities of {client_name}'},
                {'type': 'content', 'title': 'Features Overview', 'description': f'Key features include: {features}'},
                {'type': 'footer', 'title': 'Footer', 'description': 'Site footer'}
            ]
        elif 'course' in page_name_lower:
            _base('Courses', 'Explore available courses and learning paths')
            _add('filters', 'Course Filters', 'Filter by topic, level, duration, and format')
            _add('list', 'Course Listings', _summary(features, services, 'Course cards with title, rating, duration, and enrollment CTA'))
            _add('cta', 'Enroll', 'Start learning with a simple enrollment flow')
            _add('footer', 'Footer', 'Site footer')
        elif 'instructor' in page_name_lower or 'teacher' in page_name_lower:
            _base('Instructors', 'Meet the instructors and their experience')
            _add('profiles', 'Instructor Profiles', 'Bio, expertise, courses taught, and student ratings')
            _add('cta', 'Join a Class', 'Choose a course and learn from experts')
            _add('footer', 'Footer', 'Site footer')
        elif 'review' in page_name_lower or 'testimonial' in page_name_lower:
            _base('Student Reviews', 'What learners say about the experience')
            _add('testimonials', 'Testimonials', 'Ratings, quotes, and success stories')
            _add('cta', 'Get Started', 'Join learners and start your course')
            _add('footer', 'Footer', 'Site footer')
        elif 'enroll' in page_name_lower or 'registration' in page_name_lower:
            _base('Enrollment', 'Simple enrollment form and next steps')
            _add('form', 'Enrollment Form', 'Name, email, course selection, and payment details')
            _add('summary', 'Enrollment Summary', 'Selected course, pricing, and schedule')
            _add('cta', 'Confirm Enrollment', 'Complete enrollment and receive confirmation')
            _add('footer', 'Footer', 'Site footer')
        elif 'menu' in page_name_lower:
            _base('Menu', 'Explore the menu and signature dishes')
            _add('categories', 'Menu Categories', 'Starters, mains, desserts, and beverages')
            _add('specials', 'Chef Specials', _summary(features, 'Highlight signature dishes and seasonal items'))
            _add('cta', 'Reserve a Table', 'Quick reservation CTA')
            _add('footer', 'Footer', 'Site footer')
        elif 'gallery' in page_name_lower:
            _base('Gallery', 'Food, ambiance, and experience highlights')
            _add('gallery', 'Photo Gallery', 'Grid of high-quality images with lightbox view')
            _add('cta', 'Visit Us', 'Find location and reserve a table')
            _add('footer', 'Footer', 'Site footer')
        elif 'recipe' in page_name_lower and 'search' not in page_name_lower:
            _base('Recipes', 'Browse recipes and details')
            _add('list', 'Recipe Cards', 'Images, prep time, ratings, and quick actions')
            _add('detail', 'Recipe Details', _summary(features, 'Ingredients, steps, and nutrition highlights'))
            _add('cta', 'Save Recipe', 'Add to favorites or shopping list')
            _add('footer', 'Footer', 'Site footer')
        elif 'category' in page_name_lower or 'categori' in page_name_lower:
            _base('Categories', 'Browse by category')
            _add('grid', 'Category Grid', 'Tiles for popular categories and filters')
            _add('list', 'Category Items', 'Scrollable list with quick actions')
            _add('footer', 'Footer', 'Site footer')
        elif 'favorite' in page_name_lower or 'watchlist' in page_name_lower:
            _base('Favorites', 'Saved items for quick access')
            _add('list', 'Saved Items', 'Cards with actions like remove or view details')
            _add('cta', 'Discover More', 'Jump back to search or browsing')
            _add('footer', 'Footer', 'Site footer')
        elif 'search' in page_name_lower:
            _add('navbar', 'Navbar', 'Main navigation')
            page_title = ' '.join([w.capitalize() for w in page_name_lower.split()]) or 'Search'
            _add('hero', page_title, 'Find what you need fast')
            _add('search-form', 'Search Form', 'Keyword and filter controls')
            _add('filters', 'Filters', 'Refine by category, rating, price, or time')
            _add('results', 'Results', 'Grid/list with key details and actions')
            _add('footer', 'Footer', 'Site footer')
        elif 'blog' in page_name_lower or 'news' in page_name_lower:
            _base('Blog', 'Latest updates and articles')
            _add('list', 'Articles', 'Card grid with categories and tags')
            _add('cta', 'Subscribe', 'Newsletter subscription form')
            _add('footer', 'Footer', 'Site footer')
        elif 'dashboard' in page_name_lower:
            role = 'User'
            if 'admin' in page_name_lower:
                role = 'Admin'
            elif 'agent' in page_name_lower:
                role = 'Agent'
            _add('navbar', f'{role} Dashboard', f'{role} overview and quick actions')
            _add('stats', 'Key Metrics', _summary(goals, 'Bookings, revenue, cancellations, active users'))
            _add('management', 'Management', _summary(services, 'Manage items, approvals, and user actions'))
            _add('activity', 'Recent Activity', 'Latest updates and alerts')
        else:
            _base(f'{page_name_lower.title()} Page', _summary(showcase_goal, goals, features))
            if services:
                _add('content', 'Services', f'{services}')
            elif features:
                _add('content', 'Highlights', f'{features}')
            else:
                _add('content', 'Main Content', 'Primary content for this page')
            _add('footer', 'Footer', 'Site footer')

        return self._normalize_sections(page_name_lower, sections, normalized)

    def _normalize_sections(self, page_name_lower: str, sections: List[Dict[str, Any]], normalized: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Ensure unique sections, footer at end, and 5-8 sections without repeating generic fillers."""
        features = normalized.get('features', '')
        services = normalized.get('services', '')
        goals = normalized.get('goals', '')
        def _summary(*vals: Any) -> str:
            for v in vals:
                if not v:
                    continue
                if isinstance(v, list):
                    v = ', '.join([str(x).strip() for x in v if str(x).strip()])
                v = str(v).strip()
                if v:
                    return v
            return ''

        # De-dupe by title (case-insensitive)
        seen = set()
        deduped: List[Dict[str, Any]] = []
        for s in sections or []:
            title = str(s.get('title', '')).strip()
            if not title:
                continue
            key = title.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(s)

        # Move footer to the end (keep only one)
        footer = None
        rest: List[Dict[str, Any]] = []
        for s in deduped:
            if str(s.get('title', '')).strip().lower() == 'footer' or s.get('type') == 'footer':
                if not footer:
                    footer = {'type': 'footer', 'title': 'Footer', 'description': 'Site footer'}
                continue
            rest.append(s)

        # Ensure minimum 5 sections using page-specific fillers (avoid repeating generic titles)
        base_name = ' '.join([w.capitalize() for w in page_name_lower.split()]) or 'Page'
        filler_pool = [
            {'type': 'content', 'title': f'{base_name} Overview', 'description': self._title_based_section_description(f'{base_name} Overview', 'content', base_name, normalized)},
            {'type': 'content', 'title': f'{base_name} Details', 'description': self._title_based_section_description(f'{base_name} Details', 'content', base_name, normalized)},
            {'type': 'content', 'title': f'{base_name} Highlights', 'description': self._title_based_section_description(f'{base_name} Highlights', 'content', base_name, normalized)},
            {'type': 'cta', 'title': f'{base_name} Next Step', 'description': self._title_based_section_description(f'{base_name} Next Step', 'cta', base_name, normalized)},
            {'type': 'faq', 'title': f'{base_name} FAQs', 'description': self._title_based_section_description(f'{base_name} FAQs', 'faq', base_name, normalized)}
        ]

        while len(rest) < 4 and filler_pool:
            candidate = filler_pool.pop(0)
            key = candidate['title'].lower()
            if key in {s.get('title', '').lower() for s in rest}:
                continue
            rest.append(candidate)

        if footer:
            rest.append(footer)
        else:
            rest.append({'type': 'footer', 'title': 'Footer', 'description': self._title_based_section_description('Footer', 'footer', base_name, normalized)})

        # Limit to 5-8 sections
        if len(rest) > 8:
            # Always keep footer last
            footer_section = rest[-1]
            rest = rest[:7] + [footer_section]
        return rest

    def _build_pages_from_tree(self, pages_tree: List[Dict[str, Any]], normalized: Dict[str, Any]) -> List[Dict[str, Any]]:
        def build_node(node: Dict[str, Any]) -> Dict[str, Any]:
            name = self._clean_page_name(str(node.get('name', 'Page')).strip() or 'Page')
            page_name_lower = name.lower()
            children = [build_node(child) for child in node.get('children', []) if isinstance(child, dict)]
            return {
                'id': str(uuid.uuid4())[:8],
                'name': name,
                'description': self._get_page_description(page_name_lower),
                'sections': self._build_sections_for_page(page_name_lower, normalized),
                'children': children
            }

        pages = [build_node(node) for node in pages_tree if isinstance(node, dict)]
        return pages

    def generate_sitemap(self, prompt: str, brief_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate sitemap from natural language prompt or structured brief data"""
        normalized = self._normalize_brief(prompt, brief_data)
        if isinstance(normalized, dict):
            normalized['prompt_text'] = prompt or ''
        prompt_lower = (prompt or '').lower()

        if normalized:
            # If we have structured brief data or parsed prompt, prioritize it
            website_type = normalized.get('type') or self._determine_website_type(prompt_lower)
            pages_tree = normalized.get('pages_tree')
            pages_list = normalized.get('pages_list')

            if pages_tree:
                pages = self._build_pages_from_tree(pages_tree, normalized)
                if not any(p.get('name', '').lower() == 'home' for p in pages):
                    pages.insert(0, {
                        'id': str(uuid.uuid4())[:8],
                        'name': 'Home',
                        'description': 'Main landing page',
                        'sections': self._build_sections_for_page('home', normalized),
                        'children': []
                    })
            elif pages_list:
                # Strictly use provided pages
                raw_names = [str(p).strip() for p in pages_list if str(p).strip()]
                page_names = self._dedupe_pages(raw_names)
                pages = []
                for name in page_names:
                    page_id = str(uuid.uuid4())[:8]
                    page_name_lower = name.lower()
                    sections = self._build_sections_for_page(page_name_lower, normalized)

                    pages.append({
                        'id': page_id,
                        'name': name,
                        'description': self._get_page_description(page_name_lower),
                        'sections': sections,
                        'children': []
                    })
                
                # Ensure Home is prepended if not present
                if not any(p['name'].lower() == 'home' for p in pages):
                    home_id = str(uuid.uuid4())[:8]
                    home_sections = self._build_sections_for_page('home', normalized)

                    pages.insert(0, {
                        'id': home_id,
                        'name': 'Home',
                        'description': 'Main landing page',
                        'sections': home_sections,
                        'children': []
                    })
            else:
                page_count = normalized.get('page_count') or self._extract_page_count(prompt_lower)
                pages = self._generate_pages_from_prompt(prompt_lower, page_count)
        else:
            page_count = self._extract_page_count(prompt_lower)
            website_type = self._determine_website_type(prompt_lower)
            pages = self._generate_pages_from_prompt(prompt_lower, page_count)

        # AI-driven section generation with heuristic fallback when AI fails.
        if pages:
            sections_map = {}
            if config.chat_ai_enabled and config.ai_api_key:
                sections_map = self._ai_generate_sections_map(prompt, normalized or {}, pages)

            def apply_sections(nodes: List[Dict[str, Any]]):
                for node in nodes:
                    name = node.get('name', '')
                    if name in sections_map:
                        node['sections'] = self._normalize_sections(str(name).lower(), sections_map[name], normalized or {})
                    else:
                        node['sections'] = self._build_sections_for_page(str(name).lower(), normalized or {})
                    
                    # Ensure all sections have an id
                    for section in node.get('sections', []):
                        if 'id' not in section:
                            section['id'] = str(uuid.uuid4())[:8]

                    if node.get('children'):
                        apply_sections(node['children'])

            apply_sections(pages)
        
        brief_payload = {}
        if isinstance(normalized, dict):
            for key in [
                'client', 'type', 'services', 'features', 'goals', 'style', 'tone',
                'language', 'showcase', 'trip_types', 'passenger_types', 'addons',
                'payments', 'policies', 'prompt_text'
            ]:
                if normalized.get(key):
                    brief_payload[key] = normalized.get(key)

        return {
            'website_type': website_type,
            'brief': brief_payload,
            'pages': pages
        }

    def generate_questions_for_brief(self, prompt: str, ai_enabled: Any = None) -> List[Dict]:
        """Generate customized questions with dynamic options based on initial prompt analysis"""
        parsed = self.parse_prompt(prompt)
        prompt_lower = (prompt or '').lower()
        website_type = parsed.get('type') or self._determine_website_type(prompt_lower)
        intent = self._detect_intent(prompt)
        if parsed.get('type') == 'Flight Booking Website':
            intent = self.intent_hints.get('travel', intent)
        
        travel_mode = intent.get('type') == 'Flight Booking Website'

        if travel_mode:
            questions = [
                { 
                    'id': 'client', 
                    'text': f"To create a detailed sitemap and wireframe plan for your {website_type.lower()}, I'll need to gather some essential information first.\n\nWhat is the name of your company or business?", 
                    'options': [], 
                    'summaryField': 'client', 
                    'multiSelect': False 
                },
                { 'id': 'type', 'text': "Confirm the website type or specify a sub-niche:", 'options': [], 'summaryField': 'type', 'multiSelect': False },
                { 'id': 'showcase', 'text': "What is the primary function of this site?", 'options': [], 'summaryField': 'showcase', 'multiSelect': True },
                { 'id': 'services', 'text': f"What specific services will the {website_type.lower()} provide?", 'options': [], 'summaryField': 'services', 'multiSelect': True },
                { 'id': 'goals', 'text': "What are your top project goals?", 'options': [], 'summaryField': 'goals', 'multiSelect': True },
                { 'id': 'features', 'text': "Which core features should we include?", 'options': [], 'summaryField': 'features', 'multiSelect': True },
                { 'id': 'pages', 'text': "Which pages should be in your sitemap?", 'options': [], 'summaryField': 'sitemap', 'multiSelect': False },
                { 'id': 'tone', 'text': "Choose a brand personality / Tone:", 'options': [], 'summaryField': 'tone', 'multiSelect': False },
                { 'id': 'style', 'text': "Select a visual direction or color palette:", 'options': [], 'summaryField': 'style', 'multiSelect': False },
                { 'id': 'language', 'text': "Target site language:", 'options': ['English'], 'summaryField': 'language', 'multiSelect': False },
                { 'id': 'trip_types', 'text': "Which trip types should be supported?", 'options': [], 'summaryField': 'tripTypes', 'multiSelect': True },
                { 'id': 'passenger_types', 'text': "Which passenger types will you support?", 'options': [], 'summaryField': 'passengerTypes', 'multiSelect': True },
                { 'id': 'addons', 'text': "Which add-ons should users be able to select?", 'options': [], 'summaryField': 'addons', 'multiSelect': True },
                { 'id': 'payments', 'text': "Which payment methods will you accept?", 'options': [], 'summaryField': 'payments', 'multiSelect': True },
                { 'id': 'policies', 'text': "Which policies should be highlighted?", 'options': [], 'summaryField': 'policies', 'multiSelect': True }
            ]
        else:
            questions = [
                { 
                    'id': 'client', 
                    'text': f"To create a detailed sitemap and wireframe plan for your {website_type.lower()}, I'll need to gather some essential information first.\n\nWhat is the name of your company or business?", 
                    'options': [], 
                    'summaryField': 'client', 
                    'multiSelect': False 
                },
                { 'id': 'type', 'text': "Confirm the website type or specify a sub-niche:", 'options': [], 'summaryField': 'type', 'multiSelect': False },
                { 'id': 'showcase', 'text': "What is the primary function of this site?", 'options': [], 'summaryField': 'showcase', 'multiSelect': True },
                { 'id': 'services', 'text': f"What specific services will the {website_type.lower()} provide?", 'options': [], 'summaryField': 'services', 'multiSelect': True },
                { 'id': 'goals', 'text': "What are your top project goals?", 'options': [], 'summaryField': 'goals', 'multiSelect': True },
                { 'id': 'features', 'text': "Which core features should we include?", 'options': [], 'summaryField': 'features', 'multiSelect': True },
                { 'id': 'pages', 'text': "Which pages should be in your sitemap?", 'options': [], 'summaryField': 'sitemap', 'multiSelect': True },
                { 'id': 'tone', 'text': "Choose a brand personality / Tone:", 'options': [], 'summaryField': 'tone', 'multiSelect': False },
                { 'id': 'style', 'text': "Select a visual direction or color palette:", 'options': [], 'summaryField': 'style', 'multiSelect': False },
                { 'id': 'language', 'text': "Target site language:", 'options': ['English'], 'summaryField': 'language', 'multiSelect': False }
            ]
        ai_options = self._ai_suggest_options(prompt, questions, parsed, ai_enabled)
        # AI retry + lightweight inference pass: if AI returns nothing (or mostly empty),
        # run a brief extraction and merge missing fields so we avoid generic fallbacks.
        if (not ai_options or len([k for k, v in ai_options.items() if v]) < max(1, len(questions) // 3)) and config.chat_ai_enabled and config.ai_api_key:
            ai_brief = self._ai_extract_brief(prompt)
            if ai_brief:
                parsed = self._merge_missing_fields(parsed, ai_brief)
        if ai_options:
            for q in questions:
                qid = q.get('id')
                if not qid:
                    continue
                suggestions = ai_options.get(qid)
                if suggestions:
                    if qid == 'language':
                        q['options'] = ['English']
                        continue
                    q['options'] = [str(v).strip() for v in suggestions if str(v).strip()]

        # Fallback to parsed values if AI returned nothing for a question
        parsed_key_map = {
            'client': 'client',
            'type': 'type',
            'showcase': 'showcase',
            'services': 'services',
            'features': 'features',
            'goals': 'goals',
            'style': 'style',
            'tone': 'tone',
            'language': 'language',
            'pages': 'pages_text',
            'trip_types': 'trip_types',
            'passenger_types': 'passenger_types',
            'addons': 'addons',
            'payments': 'payments',
            'policies': 'policies'
        }
        for q in questions:
            if q.get('options'):
                continue
            qid = q.get('id')
            if not qid:
                continue
            if qid == 'language':
                q['options'] = ['English']
                continue
            parsed_value = parsed.get(parsed_key_map.get(qid, qid))
            if qid == 'pages' and not parsed_value:
                if isinstance(parsed.get('pages'), list):
                    parsed_value = parsed.get('pages')
            if parsed_value:
                if isinstance(parsed_value, list):
                    q['options'] = [str(v).strip() for v in parsed_value if str(v).strip()]
                else:
                    parts = [p.strip() for p in re.split(r'[,\|/;]| and ', str(parsed_value), flags=re.IGNORECASE) if p.strip()]
                    if parts:
                        q['options'] = parts

        # Final fallback: always provide at least some prompt-relevant options
        for q in questions:
            if q.get('options'):
                continue
            qid = q.get('id')
            if not qid:
                continue
            q['options'] = self._fallback_question_options(qid, prompt, parsed, website_type, intent, travel_mode)

        # Ensure at least 4 suggestions per question (except language which is fixed to English)
        def _top_up_options(qid: str, existing: List[str]) -> List[str]:
            if qid == 'language':
                return ['English']
            opts = [str(v).strip() for v in existing if str(v).strip()]
            # Add fallback suggestions
            fallback = self._fallback_question_options(qid, prompt, parsed, website_type, intent, travel_mode)
            opts.extend(fallback)
            # Add prompt-keyword-derived suggestions if still low
            if len(opts) < 4:
                keywords = self._extract_prompt_keywords(prompt, parsed)
                base = ' '.join([w.capitalize() for w in (keywords[0] if keywords else (website_type or 'Site')).split()]) if (keywords or website_type) else 'Site'
                if qid == 'showcase':
                    opts.extend([f"{base} Showcase", f"{base} Experience", f"{base} Discovery"])
                elif qid in ('services', 'features'):
                    opts.extend([f"{base} Services", f"{base} Features", f"{base} Tools"])
                elif qid == 'goals':
                    opts.extend([f"Improve {base} experience", f"Increase {base} engagement", f"Build trust in {base}"])
                elif qid == 'pages':
                    opts.extend([f"{base} Overview", f"{base} Details", "Contact"])
                elif qid == 'style':
                    opts.extend([f"{base} Modern", f"{base} Clean", f"{base} Minimal", f"{base} Bright"])
                elif qid == 'tone':
                    opts.extend([f"{base} Friendly", f"{base} Professional", f"{base} Trustworthy", f"{base} Calm"])
                else:
                    opts.extend([f"{base} Option 1", f"{base} Option 2", f"{base} Option 3", f"{base} Option 4"])
            # Dedupe while preserving order
            seen = set()
            deduped = []
            for opt in opts:
                key = opt.lower()
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(opt)
            return deduped[:5] if len(deduped) > 5 else deduped

        for q in questions:
            qid = q.get('id')
            if not qid:
                continue
            if qid == 'language':
                q['options'] = ['English']
                continue
            current_opts = q.get('options') or []
            if len(current_opts) < 4:
                q['options'] = _top_up_options(qid, current_opts)
        return questions

    def _extract_page_count(self, prompt: str) -> int:
        """Extract number of pages from prompt"""
        numbers = re.findall(r'\d+', prompt)
        if numbers:
            return min(int(numbers[0]), 20)  # Cap at 20 pages
        return 5  # Default

    def _determine_website_type(self, prompt: str) -> str:
        """Determine website type from prompt - now preserves user's full prompt"""
        if not prompt or len(prompt.strip()) < 3:
            return 'Business Website'
        
        # Clean up the prompt to use as a type name (Title Case)
        # Remove common trailing phrases if they exist to keep it clean, or keep them if they are part of the core prompt
        cleaned = prompt.strip()
        # Capitalize each word for a professional title look
        return ' '.join(word.capitalize() for word in cleaned.split())

    def _generate_pages_from_prompt(self, prompt: str, page_count: int) -> List[Dict]:
        """Generate pages based on prompt analysis"""
        pages = []
        
        # Always start with Home page
        pages.append({
            'id': str(uuid.uuid4())[:8],
            'name': 'Home',
            'description': 'Main landing page with company overview',
            'children': []
        })
        
        # Analyze prompt for specific page mentions
        mentioned_pages = self._extract_mentioned_pages(prompt)
        
        # Add mentioned pages
        for page_name in mentioned_pages:
            if len(pages) < page_count:
                pages.append({
                    'id': str(uuid.uuid4())[:8],
                    'name': page_name,
                    'description': self._get_page_description(page_name.lower()),
                    'children': []
                })
        
        # Fill remaining slots with common pages based on website type
        remaining_count = page_count - len(pages)
        common_pages = self._get_common_pages_for_type(prompt)
        
        for page_name in common_pages:
            if remaining_count > 0 and not any(p['name'].lower() == page_name.lower() for p in pages):
                pages.append({
                    'id': str(uuid.uuid4())[:8],
                    'name': page_name,
                    'description': self._get_page_description(page_name.lower()),
                    'children': []
                })
                remaining_count -= 1
        
        # Add child pages for services/products if mentioned
        self._add_child_pages(pages, prompt)
        
        return pages

    def _extract_mentioned_pages(self, prompt: str) -> List[str]:
        """Extract specific page names mentioned in the prompt"""
        # Common page patterns
        page_patterns = {
            r'\bhome\b': 'Home',
            r'\brecipe search\b': 'Recipe Search',
            r'\brecipes?\b': 'Recipes',
            r'\bcategories?\b': 'Categories',
            r'\bfavorites?\b': 'Favorites',
            r'\bcourses?\b': 'Courses',
            r'\bcourse listings?\b': 'Courses',
            r'\binstructors?\b': 'Instructors',
            r'\binstructor profiles?\b': 'Instructors',
            r'\bstudent reviews?\b': 'Student Reviews',
            r'\breviews?\b': 'Reviews',
            r'\btestimonials?\b': 'Testimonials',
            r'\benroll(ment|ments)?\b': 'Enrollment',
            r'\bteam registration\b': 'Team Registration',
            r'\bfixtures\b': 'Fixtures',
            r'\blive scores?\b': 'Live Scores',
            r'\bpoints table\b': 'Points Table',
            r'\bstandings?\b': 'Standings',
            r'\bplayer statistics\b': 'Player Statistics',
            r'\bplayer stats\b': 'Player Statistics',
            r'\bmatch results?\b': 'Match Results',
            r'\bmatch summaries?\b': 'Match Summaries',
            r'\btrending\s+movies\b': 'Trending Movies',
            r'\btrending\b': 'Trending Movies',
            r'\bfavourites?\b': 'Favorites',
            r'\bfavorites?\b': 'Favorites',
            r'\bwatchlist\b': 'Favorites',
            r'\babout\b': 'About',
            r'\bservices?\b': 'Services',
            r'\bproducts?\b': 'Products',
            r'\bportfolio\b': 'Portfolio',
            r'\bblog\b': 'Blog',
            r'\bcontact\b': 'Contact',
            r'\bpricing\b': 'Pricing',
            r'\bteam\b(?!\s+registration)': 'Team',
            r'\bcareers?\b': 'Careers',
            r'\bfaq\b': 'FAQ',
            r'\bsupport\b': 'Support',
            r'\bresources?\b': 'Resources',
            r'\bcases?\sstud(y|ies)\b': 'Case Studies',
            r'\btestimonials?\b': 'Testimonials',
            r'\bgallery\b': 'Gallery',
            r'\bnews\b': 'News'
        }

        positions = []
        for pattern, page_name in page_patterns.items():
            for match in re.finditer(pattern, prompt, re.IGNORECASE):
                positions.append((match.start(), page_name))

        positions.sort(key=lambda x: x[0])
        seen = set()
        ordered = []
        for _, page_name in positions:
            key = page_name.lower()
            if key in seen:
                continue
            seen.add(key)
            ordered.append(page_name)

        return ordered

    def _get_common_pages_for_type(self, prompt: str) -> List[str]:
        """Get common pages based on website type"""
        intent = self._detect_intent(prompt)
        if intent.get('pages'):
            return intent['pages']
        if any(word in prompt for word in ['marketing', 'agency']):
            return ['About', 'Services', 'Portfolio', 'Contact']
        elif any(word in prompt for word in ['law', 'legal']):
            return ['About', 'Practice Areas', 'Attorneys', 'Contact']
        elif any(word in prompt for word in ['restaurant', 'food']):
            return ['Menu', 'About', 'Reservations', 'Contact']
        elif any(word in prompt for word in ['ecommerce', 'shop']):
            return ['Products', 'About', 'Cart', 'Account', 'Support']
        elif any(word in prompt for word in ['portfolio', 'designer']):
            return ['Portfolio', 'About', 'Services', 'Contact']
        elif any(word in prompt for word in ['saas', 'software']):
            return ['Features', 'Pricing', 'About', 'Support', 'Contact']
        else:
            return ['About', 'Services', 'Contact']

    def _get_page_description(self, page_name: str) -> str:
        """Get description for a page based on its name"""
        descriptions = {
            'home': 'Main landing page with company overview and key information',
            'trending movies': 'Trending and popular movies list with filters and highlights',
            'favorites': 'Saved movies and personal watchlist',
            'team registration': 'Team signup and roster registration workflows',
            'fixtures': 'Match schedule and fixtures list',
            'live scores': 'Live score updates and current match status',
            'points table': 'Standings table with points and rankings',
            'standings': 'Standings table with points and rankings',
            'player statistics': 'Player stats and performance metrics',
            'match results': 'Completed match results and summaries',
            'match summaries': 'Match summaries with highlights and key stats',
            'about': 'Company background, history, mission, and team information',
            'about us': 'Company background, history, mission, and team information',
            'services': 'Services and solutions offered by the company',
            'products': 'Product catalog and detailed product information',
            'portfolio': 'Showcase of work, projects, and case studies',
            'blog': 'Blog posts, articles, and company news',
            'contact': 'Contact information, form, and office locations',
            'pricing': 'Pricing plans and package information',
            'team': 'Team members, their roles, and expertise',
            'careers': 'Job openings and career opportunities',
            'faq': 'Frequently asked questions and answers',
            'support': 'Customer support and help resources',
            'resources': 'Helpful resources, guides, and downloads',
            'case studies': 'Detailed client success stories and case studies',
            'testimonials': 'Client testimonials and reviews',
            'gallery': 'Photo gallery and visual content',
            'news': 'Latest news and company updates',
            'practice areas': 'Legal practice areas and specializations',
            'attorneys': 'Attorney profiles and expertise',
            'menu': 'Food and drink menu with prices',
            'reservations': 'Table booking and reservation system',
            'cart': 'Shopping cart and checkout process',
            'account': 'User account management and profile',
            'features': 'Product features and capabilities'
        }
        
        return descriptions.get(page_name, f'Information and content related to {page_name}')

    def _add_child_pages(self, pages: List[Dict], prompt: str):
        """Add child pages for services or products if appropriate"""
        for page in pages:
            if page['name'].lower() == 'services':
                if any(word in prompt for word in ['marketing', 'agency']):
                    page['children'] = [
                        {
                            'id': str(uuid.uuid4())[:8],
                            'name': 'Digital Marketing',
                            'description': 'SEO, PPC, and online advertising services',
                            'children': [
                                {
                                    'id': str(uuid.uuid4())[:8],
                                    'name': 'SEO Services',
                                    'description': 'Search engine optimization and organic traffic growth',
                                    'children': []
                                },
                                {
                                    'id': str(uuid.uuid4())[:8],
                                    'name': 'PPC Management',
                                    'description': 'Pay-per-click advertising campaign management',
                                    'children': []
                                }
                            ]
                        },
                        {
                            'id': str(uuid.uuid4())[:8],
                            'name': 'Content Marketing',
                            'description': 'Content strategy and creation services',
                            'children': [
                                {
                                    'id': str(uuid.uuid4())[:8],
                                    'name': 'Blog Writing',
                                    'description': 'Professional blog content creation',
                                    'children': []
                                },
                                {
                                    'id': str(uuid.uuid4())[:8],
                                    'name': 'Social Media Content',
                                    'description': 'Social media posts and campaigns',
                                    'children': []
                                }
                            ]
                        },
                        {
                            'id': str(uuid.uuid4())[:8],
                            'name': 'Brand Strategy',
                            'description': 'Brand development and positioning services',
                            'children': []
                        }
                    ]
                elif any(word in prompt for word in ['law', 'legal']):
                    page['children'] = [
                        {
                            'id': str(uuid.uuid4())[:8],
                            'name': 'Personal Injury',
                            'description': 'Personal injury law and compensation claims',
                            'children': [
                                {
                                    'id': str(uuid.uuid4())[:8],
                                    'name': 'Car Accidents',
                                    'description': 'Motor vehicle accident representation',
                                    'children': []
                                },
                                {
                                    'id': str(uuid.uuid4())[:8],
                                    'name': 'Slip & Fall',
                                    'description': 'Premises liability and slip and fall cases',
                                    'children': []
                                }
                            ]
                        },
                        {
                            'id': str(uuid.uuid4())[:8],
                            'name': 'Corporate Law',
                            'description': 'Business law and corporate legal services',
                            'children': []
                        },
                        {
                            'id': str(uuid.uuid4())[:8],
                            'name': 'Family Law',
                            'description': 'Divorce, custody, and family legal matters',
                            'children': []
                        }
                    ]
            elif page['name'].lower() == 'products':
                if any(word in prompt for word in ['ecommerce', 'shop']):
                    page['children'] = [
                        {
                            'id': str(uuid.uuid4())[:8],
                            'name': 'Electronics',
                            'description': 'Electronic devices and accessories',
                            'children': [
                                {
                                    'id': str(uuid.uuid4())[:8],
                                    'name': 'Smartphones',
                                    'description': 'Latest smartphone models and accessories',
                                    'children': []
                                },
                                {
                                    'id': str(uuid.uuid4())[:8],
                                    'name': 'Laptops',
                                    'description': 'Computers and laptop accessories',
                                    'children': []
                                }
                            ]
                        },
                        {
                            'id': str(uuid.uuid4())[:8],
                            'name': 'Clothing',
                            'description': 'Fashion and apparel collections',
                            'children': [
                                {
                                    'id': str(uuid.uuid4())[:8],
                                    'name': 'Men\'s Clothing',
                                    'description': 'Men\'s fashion and accessories',
                                    'children': []
                                },
                                {
                                    'id': str(uuid.uuid4())[:8],
                                    'name': 'Women\'s Clothing',
                                    'description': 'Women\'s fashion and accessories',
                                    'children': []
                                }
                            ]
                        }
                    ]
            elif page['name'].lower() == 'about':
                # Add sub-pages to About section
                page['children'] = [
                    {
                        'id': str(uuid.uuid4())[:8],
                        'name': 'Our Story',
                        'description': 'Company history and founding story',
                        'children': []
                    },
                    {
                        'id': str(uuid.uuid4())[:8],
                        'name': 'Team',
                        'description': 'Meet our team members and leadership',
                        'children': []
                    },
                    {
                        'id': str(uuid.uuid4())[:8],
                        'name': 'Mission & Values',
                        'description': 'Our mission statement and core values',
                        'children': []
                    }
                ]


class WireframeGenerator:
    """Service class for generating wireframes from sitemap data"""

    def _get_brief_context(self, sitemap_data: Dict[str, Any]) -> Dict[str, Any]:
        brief = sitemap_data.get('brief') if isinstance(sitemap_data, dict) else {}
        if not isinstance(brief, dict):
            brief = {}

        keys = [
            'client', 'type', 'services', 'features', 'goals', 'style', 'tone',
            'language', 'showcase', 'trip_types', 'passenger_types', 'addons',
            'payments', 'policies', 'prompt_text'
        ]
        return {key: brief.get(key, '') for key in keys if brief.get(key)}

    def _find_page_context(self, page_id: str, page_name: str, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        for page in pages or []:
            if page.get('id') == page_id:
                return page
            if str(page.get('name', '')).strip().lower() == str(page_name).strip().lower():
                return page
            children = page.get('children') or []
            if children:
                found = self._find_page_context(page_id, page_name, children)
                if found:
                    return found
        return {}

    def _brief_list(self, value: Any, fallback: List[str] = None) -> List[str]:
        if isinstance(value, list):
            items = [str(v).strip() for v in value if str(v).strip()]
            return items[:8]
        if isinstance(value, str):
            items = [part.strip() for part in re.split(r'[,\n;/]| and ', value, flags=re.IGNORECASE) if part.strip()]
            return items[:8]
        return list(fallback or [])

    def _menu_items_from_sitemap(self, sitemap_data: Dict[str, Any]) -> List[str]:
        items: List[str] = []

        def collect(nodes: List[Dict[str, Any]]) -> None:
            for node in nodes or []:
                name = str(node.get('name', '')).strip()
                if name and name not in items:
                    items.append(name)
                if len(items) >= 7:
                    return
                collect(node.get('children') or [])
                if len(items) >= 7:
                    return

        collect((sitemap_data or {}).get('pages', []) or [])
        return items or ['Home', 'About', 'Services', 'Contact']

    def _section_icon(self, section_type: str, index: int = 0) -> str:
        icon_sets = {
            'features': ['⚡', '🛡️', '📈', '🧠'],
            'services': ['🛠️', '🚀', '🎯', '📦'],
            'service': ['🛠️', '🚀', '🎯', '📦'],
            'information': ['📘', '📊', '🔍', '🧩'],
            'info': ['📘', '📊', '🔍', '🧩'],
            'pricing': ['💳', '🏷️', '🏆', '📦'],
            'testimonial': ['⭐', '💬', '🏅', '❤️'],
            'team': ['👤', '👥', '🧑‍💼', '🧑‍💻'],
            'blog': ['📰', '✍️', '📚', '🗂️'],
            'faq': ['❓', '💡', '🛟', '✅'],
            'contact': ['📍', '✉️', '📞', '🕒'],
            'contact-form': ['✉️', '📝', '📨', '💬'],
            'contact-details': ['📍', '✉️', '📞', '🕒'],
            'footer': ['🔗', '🌐', '📄', '🔒'],
            'cta': ['🎯', '🚀', '✨', '📈'],
            'hero': ['🚀', '✨', '🌟', '🎯'],
            'gallery': ['🖼️', '📷', '🎬', '📸'],
            'stats': ['📊', '📈', '🏆', '🌍'],
        }
        pool = icon_sets.get(str(section_type or '').lower(), ['✨', '📌', '🔹', '🌟'])
        return pool[index % len(pool)]

    def _section_button_text(self, section_type: str, page_name: str, brief: Dict[str, Any]) -> str:
        lower_type = str(section_type or '').lower()
        page_label = str(page_name or 'page').strip()
        showcase = str(brief.get('showcase', '') or '').strip()
        goals = str(brief.get('goals', '') or '').strip()
        if lower_type == 'navbar':
            return 'Contact Us'
        if lower_type in ('hero', 'cta'):
            if showcase:
                return showcase.split(',')[0].strip()[:32] or f'Explore {page_label}'
            if goals:
                return goals.split(',')[0].strip()[:32] or f'Explore {page_label}'
            return f'Explore {page_label}'
        if lower_type in ('pricing',):
            return 'Choose Plan'
        if lower_type in ('contact', 'contact-form'):
            return 'Send Inquiry'
        if lower_type in ('blog', 'content', 'information', 'info'):
            return 'Learn More'
        return ''

    def _title_based_section_description(self, title: str, section_type: str, page_name: str, brief: Dict[str, Any]) -> str:
        title_text = str(title or page_name).strip() or page_name
        page_label = str(page_name or 'this page').strip() or 'this page'
        client = str(brief.get('client', '') or 'the brand').strip()
        goals = self._brief_list(brief.get('goals'))
        services = self._brief_list(brief.get('services'))
        features = self._brief_list(brief.get('features'))
        focus = goals[0] if goals else (services[0] if services else (features[0] if features else page_label))
        lower_type = str(section_type or 'content').lower()

        if lower_type == 'footer':
            return f'Wraps up {page_label} with useful links, contact routes, and clear next steps for visitors exploring {client}.'
        if lower_type == 'cta':
            return f'Encourages visitors to take the next action after reviewing {title_text}, with messaging tied to {focus}.'
        if lower_type == 'faq':
            return f'Answers practical questions around {title_text} so the {page_label} experience stays clear and decision-ready.'
        if lower_type in ('content', 'information', 'info', 'main-info', 'supporting-info'):
            return f'Explains {title_text} in a way that supports {focus} and gives the {page_label} page more depth and clarity.'
        if lower_type in ('contact', 'contact-form', 'contact-details'):
            return f'Guides visitors through {title_text} with clear ways to reach {client} and move the conversation forward.'
        if lower_type in ('services', 'service'):
            return f'Presents {title_text} as a focused offer connected to {focus}, with practical value for the visitor.'
        if lower_type == 'features':
            return f'Shows how {title_text} strengthens the experience of {page_label} and supports the goals defined in the brief.'
        return f'Keeps {title_text} specific to {page_label} while reinforcing the priorities captured in the original brief.'

    def _is_generic_item_desc(self, desc: str) -> bool:
        text = str(desc or '').strip().lower()
        if not text:
            return True
        generic_patterns = [
            'professional offering tailored',
            'brings the brief into this section',
            'answer this question with concise guidance',
            'supporting information',
            'section content',
            'key project information appears here'
        ]
        return any(pattern in text for pattern in generic_patterns)

    def _describe_item(self, item_title: str, section_type: str, section_title: str, page_name: str, brief: Dict[str, Any], index: int = 0) -> str:
        item = str(item_title or '').strip() or f'Item {index + 1}'
        lower_item = item.lower()
        client = str(brief.get('client', '') or 'the business').strip()
        page_label = str(page_name or 'this page').strip()
        services = self._brief_list(brief.get('services'))
        features = self._brief_list(brief.get('features'))
        goals = self._brief_list(brief.get('goals'))
        showcase = self._brief_list(brief.get('showcase'))
        focus = services[index] if index < len(services) else (features[index] if index < len(features) else (goals[index] if index < len(goals) else 'the project goals'))
        focus_text = str(focus).strip() or 'the project goals'
        section_label = str(section_title or section_type or 'section').strip()

        def pick(options: List[str]) -> str:
            return options[index % len(options)]

        if section_type in ('services', 'service'):
            return pick([
                f'{item} positions {client} around {focus_text}, giving the {page_label} page a clearer commercial offer.',
                f'This card frames {item} as a practical service line connected to {focus_text} and the needs behind {section_label}.',
                f'{item} highlights a distinct offer for visitors who care about {focus_text}, helping {page_label} feel more concrete.'
            ])
        if section_type == 'features':
            return pick([
                f'{item} brings forward a specific benefit tied to {focus_text}, making the {page_label} experience easier to understand.',
                f'This feature turns {item} into a visible advantage for visitors comparing options on {page_label}.',
                f'{item} helps communicate why {client} stands out, especially for users looking for {focus_text}.'
            ])
        if section_type in ('information', 'info', 'content', 'main-info', 'supporting-info'):
            return pick([
                f'{item} gives this section more substance by connecting the brief to a concrete point visitors can scan quickly.',
                f'This block expands on {item} so the {page_label} page feels more informed, specific, and relevant to {focus_text}.',
                f'{item} adds context that helps users understand the value behind {focus_text} without leaving the page.'
            ])
        if section_type == 'pricing':
            return pick([
                f'{item} is positioned for teams focused on {focus_text}, with a scope that feels commercially clear.',
                f'This plan makes {item} feel easier to compare by tying it to {focus_text} and a defined value level.',
                f'{item} packages the offer around {focus_text}, helping buyers understand where it best fits.'
            ])
        if section_type == 'testimonial':
            return pick([
                f'This proof point connects {item} to real confidence-building outcomes around {focus_text}.',
                f'{item} works here as social proof, reinforcing how {client} earns trust through {focus_text}.',
                f'The testimonial angle around {item} helps validate the promise behind {focus_text} in a more human way.'
            ])
        if section_type == 'faq':
            return pick([
                f'This answer should resolve uncertainty around {item} and make the next step on {page_label} feel more obvious.',
                f'{item} is clarified here so visitors can understand the scope, expectation, and decision path more quickly.',
                f'This FAQ point turns {item} into a practical answer tied to the priorities captured in the brief.'
            ])
        if section_type == 'blog':
            return pick([
                f'{item} opens a useful editorial angle connected to {focus_text} and the wider story of {page_label}.',
                f'This post idea uses {item} to deepen the content strategy around {focus_text}.',
                f'{item} becomes a relevant publishing topic here, giving the section a clearer narrative purpose.'
            ])
        if section_type in ('contact', 'contact-details'):
            if 'email' in lower_item:
                return pick([
                    f'Use this inbox for new enquiries related to {page_label} and follow-up conversations with interested visitors.',
                    f'This email route keeps project questions about {focus_text} easy to send and easy to track.',
                    f'Make this the primary written contact point for visitors reaching out through {page_label}.'
                ])
            if 'phone' in lower_item:
                return pick([
                    f'Present this as the direct line for fast consultations and time-sensitive enquiries.',
                    f'This phone contact supports immediate conversations around {focus_text} and next steps.',
                    f'Use this number for visitors who prefer a quick conversation before committing.'
                ])
            if 'hours' in lower_item:
                return pick([
                    f'Show when the team is available to respond to enquiries related to {focus_text}.',
                    f'These hours help set response expectations for visitors engaging through {page_label}.',
                    f'Use this line to communicate clear availability for follow-up and support.'
                ])
            if 'location' in lower_item or 'address' in lower_item:
                return pick([
                    f'Use this location detail to anchor {client} in a real-world setting and support trust.',
                    f'This address gives visitors a clear reference point for visiting, delivery, or local credibility.',
                    f'Present the business location in a way that strengthens legitimacy and context.'
                ])
        if section_type == 'contact-form':
            return pick([
                f'Capture {item.lower()} here so the team can reply with the right context around {focus_text}.',
                f'This field helps tailor the response and keeps enquiries about {focus_text} better qualified.',
                f'Use {item.lower()} to make follow-up communication clearer and more relevant.'
            ])
        if section_type == 'footer':
            return pick([
                f'Use this footer item to guide visitors toward the most useful follow-up links for {page_label}.',
                f'This footer block supports continuity by connecting {page_label} to the next relevant destination.',
                f'Keep this footer reference practical, scannable, and aligned with what users may need next.'
            ])
        return pick([
            f'{item} gives the {page_label} page a more specific message tied to {focus_text}.',
            f'Use {item} here to make the section feel less generic and more grounded in the project brief.',
            f'{item} adds a clearer point of emphasis for visitors exploring {page_label}.'
        ])

    def _section_items_from_brief(self, section_type: str, section_title: str, page_name: str, brief: Dict[str, Any]) -> List[Dict[str, Any]]:
        lower_type = str(section_type or '').lower()
        services = self._brief_list(brief.get('services'))
        features = self._brief_list(brief.get('features'))
        goals = self._brief_list(brief.get('goals'))
        showcase = self._brief_list(brief.get('showcase'))
        payments = self._brief_list(brief.get('payments'))
        policies = self._brief_list(brief.get('policies'))
        client = str(brief.get('client', '') or 'the business').strip()
        page_label = str(page_name or 'this page').strip()

        if lower_type == 'features':
            base = features or services or goals or [f'{page_label} advantage', 'Guided experience', 'Clear next steps']
            return [
                {
                    'title': item.title() if item.islower() else item,
                    'desc': self._describe_item(item, 'features', section_title, page_label, brief, idx),
                    'icon': self._section_icon('features', idx)
                }
                for idx, item in enumerate(base[:4])
            ]

        if lower_type in ('services', 'service'):
            base = services or features or [f'{page_label} consulting', f'{page_label} execution', f'{page_label} support']
            return [
                {
                    'title': item.title() if item.islower() else item,
                    'desc': self._describe_item(item, 'services', section_title, page_label, brief, idx),
                    'icon': self._section_icon('services', idx)
                }
                for idx, item in enumerate(base[:4])
            ]

        if lower_type == 'pricing':
            seeds = services[:3] if services else ['Starter', 'Growth', 'Premium']
            prices = ['$49', '$129', '$249']
            return [
                {
                    'title': seed.title() if seed.islower() else seed,
                    'desc': f'Best for teams focused on {goals[idx] if idx < len(goals) else "steady growth"}.',
                    'price': prices[idx] if idx < len(prices) else '$199',
                    'tag': 'POPULAR' if idx == 1 else '',
                    'features': (features[:3] if features else ['Priority support', 'Guided onboarding', 'Clear reporting'])
                }
                for idx, seed in enumerate(seeds[:3])
            ]

        if lower_type == 'testimonial':
            proof_points = goals or showcase or services or ['measurable results', 'clear delivery', 'strong communication']
            roles = ['Founder', 'Marketing Lead', 'Operations Manager']
            return [
                {
                    'title': f'{client} Client {idx + 1}',
                    'desc': self._describe_item(point, 'testimonial', section_title, page_label, brief, idx),
                    'role': roles[idx % len(roles)],
                    'icon': self._section_icon('testimonial', idx)
                }
                for idx, point in enumerate(proof_points[:3])
            ]

        if lower_type in ('information', 'info', 'content', 'main-info', 'supporting-info'):
            base = showcase or goals or features or services or [section_title, f'About {page_label}', 'Why it matters']
            return [
                {
                    'title': item.title() if item.islower() else item,
                    'desc': self._describe_item(item, lower_type, section_title, page_label, brief, idx),
                    'icon': self._section_icon('information', idx)
                }
                for idx, item in enumerate(base[:4])
            ]

        if lower_type in ('contact', 'contact-details'):
            contact_items = [
                {'title': 'Email', 'desc': f'hello@{re.sub(r"[^a-z0-9]+", "", client.lower()) or "business"}.com'},
                {'title': 'Phone', 'desc': '+1 (555) 123-4567'},
                {'title': 'Hours', 'desc': 'Mon-Fri, 9AM-6PM'},
                {'title': 'Location', 'desc': f'{client} studio or office location'}
            ]
            for idx, item in enumerate(contact_items):
                item['icon'] = self._section_icon('contact', idx)
            return contact_items

        if lower_type == 'contact-form':
            fields = ['Full Name', 'Email Address', 'Company', 'Project Details']
            return [{'title': field, 'icon': self._section_icon('contact-form', idx)} for idx, field in enumerate(fields)]

        if lower_type == 'faq':
            base = policies or goals or services or [f'What does {client} offer?', f'How does {page_label} work?', 'What happens next?']
            return [
                {
                    'title': item if item.endswith('?') else f'{item}?',
                    'desc': self._describe_item(item, 'faq', section_title, page_label, brief, idx),
                    'icon': self._section_icon('faq', idx)
                }
                for idx, item in enumerate(base[:4])
            ]

        if lower_type == 'blog':
            base = features or services or showcase or [f'{page_label} update', f'{client} insight', 'Latest perspective']
            return [
                {
                    'title': item.title() if item.islower() else item,
                    'desc': self._describe_item(item, 'blog', section_title, page_label, brief, idx),
                    'tag': f'Article {idx + 1}'
                }
                for idx, item in enumerate(base[:3])
            ]

        return []

    def _section_description_from_brief(self, section: Dict[str, Any], page_name: str, brief: Dict[str, Any]) -> str:
        existing = str(section.get('description', '') or '').strip()
        if existing and not self._is_generic_item_desc(existing) and existing.lower() != 'site footer':
            return existing
        title = str(section.get('title', '') or page_name).strip()
        section_type = str(section.get('type', 'content') or 'content').lower()
        services = ', '.join(self._brief_list(brief.get('services')))
        goals = ', '.join(self._brief_list(brief.get('goals')))
        features = ', '.join(self._brief_list(brief.get('features')))
        client = str(brief.get('client', '') or 'the business').strip()
        summary = services or features or goals or f'the goals for {page_name}'
        if section_type == 'hero':
            return f'Introduces {client} with a clear value proposition focused on {summary}.'
        if section_type in ('features', 'services', 'service'):
            return f'Breaks down the strongest points for {page_name}, grounded in {summary}.'
        if section_type in ('pricing',):
            return f'Presents commercial options connected to the scope, goals, and services in the brief.'
        if section_type in ('contact', 'contact-form', 'contact-details'):
            return f'Helps visitors contact {client} with confidence and clear next steps.'
        if section_type in ('testimonial',):
            return f'Reinforces credibility with proof points related to {summary}.'
        if section_type in ('footer',):
            return self._title_based_section_description(title, section_type, page_name, brief)
        return self._title_based_section_description(title, section_type, page_name, brief)

    def _finalize_wireframe_sections(self, sections: List[Dict[str, Any]], page: Dict[str, Any], sitemap_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        brief = self._get_brief_context(sitemap_data)
        menu_items = self._menu_items_from_sitemap(sitemap_data)
        page_name = str(page.get('name', 'Page')).strip() or 'Page'
        finalized: List[Dict[str, Any]] = []

        for idx, raw_section in enumerate(sections or []):
            if not isinstance(raw_section, dict):
                continue
            section = dict(raw_section)
            section_type = str(section.get('type', 'content') or 'content').strip().lower()
            section['id'] = section.get('id') or str(uuid.uuid4())[:8]
            section['title'] = str(section.get('title', '') or f'{page_name} Section {idx + 1}').strip()
            section['description'] = self._section_description_from_brief(section, page_name, brief)
            section['layoutVariant'] = str(section.get('layoutVariant', '') or 'layout-default').strip()

            if section_type == 'navbar':
                section['menuItems'] = [str(item).strip() for item in (section.get('menuItems') or menu_items)[:7] if str(item).strip()]
            else:
                section['menuItems'] = [str(item).strip() for item in section.get('menuItems', [])[:8] if str(item).strip()] if isinstance(section.get('menuItems'), list) else []

            if not section.get('buttonText'):
                section['buttonText'] = self._section_button_text(section_type, page_name, brief)

            items = self._normalize_wireframe_items(section.get('items', []))
            if not items:
                items = self._normalize_wireframe_items(self._section_items_from_brief(section_type, section['title'], page_name, brief))

            if section_type == 'footer' and not items:
                items = [
                    {'title': 'Company', 'desc': ', '.join(menu_items[:4]), 'icon': self._section_icon('footer', 0)},
                    {'title': 'Support', 'desc': 'Contact, FAQ, and follow-up actions', 'icon': self._section_icon('footer', 1)},
                    {'title': 'Policies', 'desc': ', '.join(self._brief_list(brief.get('policies'), ['Privacy', 'Terms'])[:3]), 'icon': self._section_icon('footer', 2)}
                ]

            refreshed_items = []
            for item_idx, item in enumerate(items):
                item_copy = dict(item)
                item_title = item_copy.get('title') or item_copy.get('label') or f'Item {item_idx + 1}'
                if self._is_generic_item_desc(item_copy.get('desc', '')):
                    item_copy['desc'] = self._describe_item(item_title, section_type, section['title'], page_name, brief, item_idx)
                if not item_copy.get('icon'):
                    item_copy['icon'] = self._section_icon(section_type, item_idx)
                refreshed_items.append(item_copy)

            section['items'] = refreshed_items
            finalized.append(section)

        return finalized

    def _normalize_wireframe_items(self, items: Any) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        if not isinstance(items, list):
            return normalized

        for item in items[:8]:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    normalized.append({'title': text, 'desc': ''})
                continue

            if not isinstance(item, dict):
                continue

            normalized.append({
                'title': str(item.get('title', '') or item.get('name', '')).strip(),
                'desc': str(item.get('desc', '') or item.get('description', '') or item.get('quote', '')).strip(),
                'role': str(item.get('role', '')).strip(),
                'price': str(item.get('price', '')).strip(),
                'tag': str(item.get('tag', '')).strip(),
                'icon': str(item.get('icon', '')).strip(),
                'label': str(item.get('label', '')).strip(),
                'value': str(item.get('value', '')).strip(),
                'features': [str(feature).strip() for feature in item.get('features', [])[:8] if str(feature).strip()] if isinstance(item.get('features'), list) else [],
            })

        return normalized
    
    def generate_wireframes(self, sitemap_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate wireframes for each page in the sitemap"""
        wireframes = {}
        
        def process_pages(pages: List[Dict], parent_path: str = ""):
            for page in pages:
                page_path = f"{parent_path}/{page['name']}" if parent_path else page['name']
                wireframes[page['id']] = self._generate_page_wireframe(page, page_path, sitemap_data)
                
                if page.get('children'):
                    process_pages(page['children'], page_path)
        
        process_pages(sitemap_data.get('pages', []))
        
        return {
            'website_type': sitemap_data.get('website_type', ''),
            'brief': self._get_brief_context(sitemap_data),
            'wireframes': wireframes
        }

    def _ai_generate_page_wireframe(self, page: Dict[str, Any], sitemap_data: Dict[str, Any]) -> List[Dict]:
        """Uses the configured OpenRouter-compatible OpenAI client to generate a wireframe layout."""
        if not config.chat_ai_enabled:
            return []
        api_key = config.ai_api_key
        if not api_key or OpenAI is None:
            return []

        base_url = config.wireframe_ai_base_url or config.chat_ai_base_url
        model = config.wireframe_ai_model or config.chat_ai_model
        if not base_url or not model:
            return []

        page_name = page.get('name', 'Page')
        page_id = page.get('id', '')
        website_type = sitemap_data.get('website_type', 'Website')
        normalized_base_url = base_url.rstrip('/')
        if normalized_base_url.endswith('/chat/completions'):
            normalized_base_url = normalized_base_url[:-len('/chat/completions')]

        pages = sitemap_data.get('pages', []) or []
        page_names = []

        def collect_page_names(nodes: List[Dict[str, Any]]) -> None:
            for node in nodes:
                name = str(node.get('name', '')).strip()
                if name:
                    page_names.append(name)
                children = node.get('children') or []
                if children:
                    collect_page_names(children)

        collect_page_names(pages)
        sitemap_context = ", ".join(page_names[:20]) if page_names else "Home"
        brief_context = self._get_brief_context(sitemap_data)
        page_context = self._find_page_context(page_id, page_name, pages) or page
        source_sections = page_context.get('sections') or page.get('sections') or []
        normalized_sections = []
        for idx, section in enumerate(source_sections):
            if not isinstance(section, dict):
                continue
            normalized_sections.append({
                'id': section.get('id') or f'section-{idx + 1}',
                'type': section.get('type', 'content'),
                'title': section.get('title', 'Section'),
                'description': section.get('description', ''),
                'layoutVariant': section.get('layoutVariant', 'layout-default'),
            })

        system_msg = (
            "You are an expert UI/UX designer and website copy strategist. Generate realistic, professional "
            "wireframe sections with high-quality content that match the provided sitemap page and brief. "
            "Return only a valid JSON array. No markdown, no explanation."
        )
        user_msg = (
            f"Generate a structured wireframe layout for the page '{page_name}' in a '{website_type}'.\n"
            f"Website sitemap pages: {sitemap_context}\n"
            f"Page description: {page_context.get('description', '')}\n\n"
            "You must enrich the EXISTING page sections below. Keep the same section count and keep each section matched "
            "to its original purpose and order. Do not invent unrelated sections and do not repeat the same message across sections.\n\n"
            f"Brief context:\n{json.dumps(brief_context, ensure_ascii=True)}\n\n"
            f"Source sections:\n{json.dumps(normalized_sections, ensure_ascii=True)}\n\n"
            "Return a JSON array with one object for each source section. Each object must include:\n"
            "- \"type\": section type\n"
            "- \"title\": section title refined for the page\n"
            "- \"description\": concise, specific copy matched to this section and the user brief\n"
            "- \"layoutVariant\": layout hint such as layout-default, layout-split-left, layout-centered, layout-grid-3, layout-list\n\n"
            "Optional fields to include whenever useful:\n"
            "- \"buttonText\": CTA label for hero, CTA, pricing, contact, banner sections\n"
            "- \"menuItems\": array of nav labels for navbar sections, based on the sitemap pages\n"
            "- \"items\": array of cards/list entries for features, services, pricing, team, testimonials, stats, blog, faq, information and footer columns\n\n"
            "For \"items\", prefer objects like:\n"
            "{\"title\":\"...\",\"desc\":\"...\",\"icon\":\"...\"}\n"
            "You may also add \"role\", \"price\", \"tag\", \"label\", \"value\", or \"features\" when relevant.\n\n"
            "Rules:\n"
            "- Make every section distinct. Avoid repeated headlines, repeated descriptions, and repeated CTA text.\n"
            "- Match the content to the user brief, services, goals, tone, and page purpose.\n"
            "- If the section is navbar, use real menu items from the sitemap.\n"
            "- If the section is pricing, testimonial, faq, features, services, blog, team, or information, always include useful \"items\".\n"
            "- If the section is contact or contact-form, include realistic contact fields or contact detail items.\n"
            "- Do not use lorem ipsum or generic filler like Feature 1, Point 1, Testimonial 1, or Contact information.\n"
            "- The result must look premium and presentation-ready."
        )

        try:
            client = OpenAI(
                base_url=normalized_base_url,
                api_key=api_key,
                default_headers={
                    'HTTP-Referer': config.ai_http_referer,
                    'X-Title': config.ai_app_name,
                }
            )

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_msg},
                    {'role': 'user', 'content': user_msg}
                ],
                temperature=0.3,
                max_tokens=1500,
                extra_body={"reasoning": {"enabled": True}}
            )

            content = response.choices[0].message.content or ''

            if content.startswith('```'):
                content = content.replace('```json', '', 1)
                content = content.replace('```', '')
            content = content.strip()

            parsed_json = json.loads(content)
            if isinstance(parsed_json, list):
                cleaned = []
                for idx, s in enumerate(parsed_json):
                    if not isinstance(s, dict):
                        continue
                    source_section = normalized_sections[idx] if idx < len(normalized_sections) else {}
                    section_type = s.get('type') or source_section.get('type', 'content')
                    section_title = s.get('title') or source_section.get('title', 'Section')
                    section_description = s.get('description') or source_section.get('description', '')
                    layout_variant = s.get('layoutVariant') or source_section.get('layoutVariant', 'layout-default')
                    cleaned.append({
                        'id': source_section.get('id') or str(uuid.uuid4())[:8],
                        'type': section_type,
                        'title': section_title,
                        'description': section_description,
                        'layoutVariant': layout_variant,
                        'buttonText': s.get('buttonText', ''),
                        'menuItems': [str(item).strip() for item in s.get('menuItems', [])[:8] if str(item).strip()] if isinstance(s.get('menuItems'), list) else [],
                        'items': self._normalize_wireframe_items(s.get('items', []))
                    })
                if cleaned and len(cleaned) == len(normalized_sections):
                    return self._finalize_wireframe_sections(cleaned, page_context, sitemap_data)
        except Exception as e:
            if 'localhost' in base_url or '127.0.0.1' in base_url:
                print(f"Local wireframe model failed ({e}); falling back to sitemap-based sections.")
            print(f"Error in wireframe AI generation: {e}")

        return []

    def _generate_page_wireframe(self, page: Dict, page_path: str, sitemap_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate wireframe structure for a single page using AI layout logic and fallback to sitemap sections"""
        page_name = page['name']
        sitemap_data = sitemap_data or {}
        
        # 1. Try AI generation first
        ai_sections = self._ai_generate_page_wireframe(page, sitemap_data)
        if ai_sections:
            return {
                'page_name': page_name,
                'page_path': page_path,
                'sections': self._finalize_wireframe_sections(ai_sections, page, sitemap_data)
            }

        # 2. Fallback to sections provided from the sitemap (already mapped)
        if 'sections' in page and page['sections']:
            sections = []
            for section in page['sections']:
                sections.append({
                    'id': section.get('id') or str(uuid.uuid4())[:8],
                    'type': section.get('type', 'content'),
                    'title': section.get('title', 'Section'),
                    'description': section.get('description', ''),
                    'layoutVariant': section.get('layoutVariant', 'layout-default'),
                    'buttonText': section.get('buttonText', ''),
                    'menuItems': section.get('menuItems', []),
                    'items': section.get('items', [])
                })
            
            return {
                'page_name': page['name'],
                'page_path': page_path,
                'sections': self._finalize_wireframe_sections(sections, page, sitemap_data)
            }



        if 'home' in page_name or page_name == 'home':
            sections = [
                {
                    'type': 'navbar',
                    'title': 'Navigation Bar',
                    'description': 'Navigation bar with company logo, main menu items (Home, About, Services, Contact), and prominent call-to-action button. Responsive design with mobile hamburger menu.'
                },
                {
                    'type': 'hero',
                    'title': 'Hero Header',
                    'description': 'Hero section with compelling headline about company value proposition, supporting subtext explaining key benefits, hero image or video background, and primary call-to-action button. Includes trust indicators like client logos or testimonials.'
                },
                {
                    'type': 'features',
                    'title': 'Core Features',
                    'description': 'Features grid showcasing 3-4 key services or benefits with icons, headlines, and descriptions. Each feature includes visual icon, benefit-focused headline, and 2-3 sentence description of value provided.'
                },
                {
                    'type': 'testimonial',
                    'title': 'Client Testimonials',
                    'description': 'Client testimonials carousel with customer photos, quotes highlighting results achieved, company names and titles. Includes star ratings and specific metrics or outcomes when possible.'
                },
                {
                    'type': 'content',
                    'title': 'Additional Information',
                    'description': 'Additional content sections including company overview, value propositions, recent work showcase, and secondary call-to-action. May include statistics, awards, or certifications.'
                },
                {
                    'type': 'footer',
                    'title': 'Site Footer',
                    'description': 'Footer with contact information, social media links, secondary navigation, newsletter signup, and legal links. Organized in columns with company info, services, resources, and contact details.'
                }
            ]
        elif 'about' in page_name:
            sections = [
                {
                    'type': 'navbar',
                    'title': 'Navigation Bar',
                    'description': 'Navigation bar consistent with site design, highlighting About page in menu'
                },
                {
                    'type': 'hero',
                    'title': 'About Hero',
                    'description': 'About page header with company mission statement, founding story introduction, and team photo or company image'
                },
                {
                    'type': 'story',
                    'title': 'Our Story',
                    'description': 'Company story section with timeline of key milestones, founding story, growth journey, and mission evolution. Includes historical photos and achievement highlights.'
                },
                {
                    'type': 'team',
                    'title': 'Meet the Team',
                    'description': 'Team section with member photos, names, roles, and brief bios. Organized in grid layout with hover effects revealing additional information about expertise and background.'
                },
                {
                    'type': 'culture',
                    'title': 'Culture & Values',
                    'description': 'Company values and culture information including core values, work philosophy, community involvement, and what makes the company unique. May include office photos and culture highlights.'
                },
                {
                    'type': 'footer',
                    'title': 'Site Footer',
                    'description': 'Footer with contact information, career opportunities link, and social media profiles'
                }
            ]
        elif 'services' in page_name or 'products' in page_name:
            sections = [
                {
                    'type': 'navbar',
                    'title': 'Navigation Bar',
                    'description': 'Navigation bar with Services/Products highlighted in menu'
                },
                {
                    'type': 'hero',
                    'title': 'Service Overview',
                    'description': f'{page["name"]} page header with overview of offerings, key benefits, and how services solve customer problems'
                },
                {
                    'type': 'content',
                    'title': 'Our Offerings',
                    'description': f'{page["name"]} grid layout with cards showing different offerings. Each card includes service icon, name, description, key features, and pricing or "Learn More" button.'
                },
                {
                    'type': 'features',
                    'title': 'Detailed Process',
                    'description': 'Detailed feature comparison or service breakdown showing what\'s included, process overview, and unique differentiators compared to competitors.'
                },
                {
                    'type': 'content',
                    'title': 'Service Packages',
                    'description': 'Pricing information or service packages with clear tiers, what\'s included in each level, and prominent call-to-action buttons for each option.'
                },
                {
                    'type': 'footer',
                    'title': 'Site Footer',
                    'description': 'Footer with contact information for consultations and links to additional resources'
                }
            ]
        elif 'contact' in page_name:
            sections = [
                {
                    'type': 'navbar',
                    'title': 'Navigation Bar',
                    'description': 'Navigation bar with Contact highlighted in menu'
                },
                {
                    'type': 'hero',
                    'title': 'Get In Touch',
                    'description': 'Contact page header with "get in touch" message, response time expectations, and preferred contact methods'
                },
                {
                    'type': 'contact',
                    'title': 'Contact Form',
                    'description': 'Contact form with fields for name, email, phone, subject, and detailed message. Includes form validation, privacy notice, and clear submit button.'
                },
                {
                    'type': 'information',
                    'title': 'Contact Details',
                    'description': 'Contact information including office address, phone numbers, email addresses, business hours, and response time expectations. Formatted for easy scanning.'
                },
                {
                    'type': 'location',
                    'title': 'Our Location',
                    'description': 'Interactive map showing office location with directions link, nearby landmarks, and parking information. May include multiple office locations if applicable.'
                },
                {
                    'type': 'footer',
                    'title': 'Site Footer',
                    'description': 'Footer with social media links, additional contact options, and emergency contact information if relevant'
                }
            ]
        elif 'blog' in page_name or 'news' in page_name:
            sections = [
                {
                    'type': 'navbar',
                    'title': 'Navigation Bar',
                    'description': 'Navigation bar with Blog/News highlighted in menu'
                },
                {
                    'type': 'hero',
                    'title': 'Featured Posts',
                    'description': 'Blog header with featured article, search functionality, and categories overview. Includes recent posts highlight and subscription options.'
                },
                {
                    'type': 'content',
                    'title': 'Article Grid',
                    'description': 'Blog post grid with article thumbnails, titles, excerpts, author information, publication dates, and read time estimates. Includes filtering and sorting options.'
                },
                {
                    'type': 'content',
                    'title': 'Blog Sidebar',
                    'description': 'Categories sidebar with popular topics, recent posts section, author profiles, and search functionality. May include tag cloud and archive links.'
                },
                {
                    'type': 'content',
                    'title': 'Navigation & Signup',
                    'description': 'Pagination controls for browsing posts, newsletter signup form, and social sharing options. Includes related articles and recommended reading.'
                },
                {
                    'type': 'footer',
                    'title': 'Site Footer',
                    'description': 'Footer with blog categories, RSS feed link, and social sharing options for content promotion'
                }
            ]
        else:
            # Generic page structure with enhanced descriptions
            sections = [
                {
                    'type': 'navbar',
                    'title': 'Navigation Bar',
                    'description': f'Navigation bar with {page["name"]} highlighted in main menu, maintaining consistent site navigation'
                },
                {
                    'type': 'hero',
                    'title': f'{page["name"]} Header',
                    'description': f'{page["name"]} page header with clear title, descriptive subtitle explaining page purpose, and relevant background image or graphic'
                },
                {
                    'type': 'information',
                    'title': 'Main Information',
                    'description': f'Main content area for {page["name"]} with relevant information, organized sections, visual elements, and clear information hierarchy. Content is scannable with headers, bullet points, and visual breaks.'
                },
                {
                    'type': 'information',
                    'title': 'Supporting Content',
                    'description': f'Additional content sections with supporting information, related resources, and call-to-action elements relevant to {page["name"]} objectives. May include FAQs, resources, or next steps.'
                },
                {
                    'type': 'footer',
                    'title': 'Site Footer',
                    'description': 'Footer with navigation links, contact information, and relevant page-specific resources or related pages'
                }
            ]
        # Ensure all statically defined sections have an ID
        for section in sections:
            if 'id' not in section:
                section['id'] = str(uuid.uuid4())[:8]
                
        return {
            'page_name': page['name'],
            'page_path': page_path,
            'sections': self._finalize_wireframe_sections(sections, page, sitemap_data)
        }

    def regenerate_section_description(self, title: str, section_type: str) -> str:
        """Provide a fresh, varied description for a section"""
        import random
        
        # Variations based on type and title
        variations = {
            'navbar': [
                "A clean, sticky navigation bar featuring your brand logo on the left and primary links (Home, Services, About, Contact) on the right. Includes a prominent CTA button for immediate user conversion.",
                "Modern, transparent navigation bar that transitions to a solid background on scroll. Features drop-down menus for services and a search bar for easy site navigation.",
                "Minimalist navigation structure with a centered logo and evenly spaced menu items. Optimized for mobile with a smooth-animating hamburger menu."
            ],
            'hero': [
                f"Impactful hero section for {title} featuring a bold headline, a persuasive sub-headline that explains your unique value proposition, and two contrasting CTA buttons to guide user action.",
                f"Dynamic hero area with a high-quality background video, a centered mission statement for {title}, and a scroll-down indicator to improve user flow.",
                f"Visually striking hero header with a split layout: on the left, a benefit-driven headline for {title}; on the right, an interactive element or product showcase image."
            ],
            'features': [
                "An elegant features grid showcasing 3 to 6 key benefits. Each item includes a modern icon, a snappy headline, and a 2-sentence description focusing on the 'why' behind each feature.",
                "Side-by-side alternating feature blocks with large, illustrative images and detailed copy explaining how each capability solves a specific customer pain point.",
                "Interactive feature tabs or accordion that allow users to explore different aspects of the service without leaving the current view."
            ],
            'services': [
                f"A comprehensive services showcase for {title} using card-based design. Each card highlights a specific offering with price indicators, key deliverables, and a 'View Details' link.",
                f"Service-focused layout for {title} featuring customer-centric descriptions, process steps (How it works), and integrated booking functionality.",
                f"Minimalist service list with clean typography and hover effects that reveal deeper information about the specific offerings in {title}."
            ],
            'testimonial': [
                "Single, high-impact testimonial section with a large quote from a key client, their professional headshot, and a link to a detailed case study.",
                "Multi-card testimonial slider showcasing varied client success stories, complete with star ratings, verified badges, and company logos.",
                "Social proof wall featuring a grid of customer tweets, video testimonials, and trust pilot ratings to build immediate credibility."
            ],
            'contact': [
                "Minimalist contact section with a split screen: a simple, multi-step form on one side and direct contact details (email, phone, social) on the other.",
                "Full-width interactive map showing your office location, paired with business hours and a 'Get Directions' button.",
                "Conversational contact area using a large, friendly header and multiple contact options categorized by inquiry type (Support, Sales, Press)."
            ],
            'footer': [
                "Informative footer organized into four columns: Company Info, Quick Links, Services, and Resources. Includes social icons and a newsletter signup field.",
                "Minimalist footer with a centered logo, copyright notice, and essential legal links (Privacy Policy, Terms). Best for landing pages.",
                "Feature-rich footer with a miniature site map, contact details, latest blog posts preview, and brand trust certifications."
            ],
            'content': [
                f"A versatile content block for {title} incorporating a balanced mix of professional copy, bulleted lists for readability, and supporting visual elements.",
                f"Detailed information section for {title} using a clean, multi-column layout to present complex data or stories in an easy-to-digest format.",
                f"Engagement-focused content area for {title} with a prominent section header, explanatory text, and a context-specific call to action."
            ]
        }
        
        # Get list of variations for the type, default to 'content' if type not found
        options = variations.get(section_type, variations['content'])
        
        # Return a random variation
        return random.choice(options)
