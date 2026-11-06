"""
backend/sitemap_app/analyzer.py
Requirement Analyzer Engine for Website Design Automation System.
Phase 3 — Requirement Analysis & Sitemap Generation

Extracts and synthesizes:
1. Website category & canonical industry taxonomy
2. Business objectives & primary conversion goals
3. Target audience & user personas
4. Design preferences (visual style, tone of voice, theme direction)
5. Required functionality & interactive capabilities
6. Required pages & hierarchical path structures
7. Navigation requirements (primary nav, footer nav, CTA)
8. Content requirements & key proof points
"""

from __future__ import annotations
import re
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from core.config import config
from .providers import CompletionRequest, execute_completion_with_fallback


class RequirementAnalyzer:
    """
    Intelligent Requirement Analyzer that transforms natural language prompts
    and brief updates into a structured, validated specification.
    """

    # Industry Taxonomy & Semantic Keywords
    CATEGORIES: Dict[str, Dict[str, Any]] = {
        'ecommerce': {
            'label': 'E-commerce Website',
            'keywords': ['shop', 'store', 'ecommerce', 'e-commerce', 'cart', 'checkout', 'products', 'apparel', 'merchandise', 'retail', 'buy online', 'goods'],
            'default_pages': ['Home', 'Shop', 'Categories', 'Product Details', 'Cart', 'Checkout', 'Account', 'Support'],
            'default_objectives': ['Drive product discovery and online purchase conversions', 'Build customer retention through streamlined checkout'],
            'default_audience': 'Online shoppers looking for quality products with seamless purchase experience',
            'default_functionality': ['Product catalog with filters and search', 'Shopping cart & secure checkout', 'Customer reviews & ratings', 'Order tracking'],
            'default_nav': ['Home', 'Shop', 'Categories', 'About Us', 'Contact'],
            'default_cta': 'Shop Now'
        },
        'saas': {
            'label': 'SaaS Platform Website',
            'keywords': ['saas', 'software', 'platform', 'cloud', 'api', 'dashboard', 'b2b tool', 'workflow automation', 'devops', 'enterprise app'],
            'default_pages': ['Home', 'Features', 'Solutions', 'Pricing', 'Documentation', 'About', 'Contact'],
            'default_objectives': ['Acquire qualified product trial signups', 'Demonstrate platform ROI and technical capability'],
            'default_audience': 'Product managers, developers, and enterprise decision-makers',
            'default_functionality': ['Interactive feature demos', 'Tiered pricing matrix with monthly/annual switch', 'API documentation portal', 'User authentication / signup'],
            'default_nav': ['Features', 'Solutions', 'Pricing', 'Docs', 'Contact'],
            'default_cta': 'Start Free Trial'
        },
        'business': {
            'label': 'Business & Corporate Website',
            'keywords': ['business', 'corporate', 'consulting', 'advisory', 'firm', 'financial', 'insurance', 'logistics', 'b2b', 'enterprise', 'management', 'commercial'],
            'default_pages': ['Home', 'About Us', 'Services', 'Case Studies', 'Insights', 'Careers', 'Contact'],
            'default_objectives': ['Establish market authority and institutional trust', 'Generate high-value enterprise consultation inquiries', 'Showcase measurable client ROI'],
            'default_audience': 'C-suite executives, corporate procurement leaders, and business partners',
            'default_functionality': ['Consultation request form', 'Case study portfolio with metric badges', 'Leadership team profiles', 'Downloadable whitepapers'],
            'default_nav': ['Home', 'About', 'Services', 'Case Studies', 'Insights', 'Contact'],
            'default_cta': 'Book Consultation'
        },
        'corporate': {
            'label': 'Corporate & Business Website',
            'keywords': ['corporate', 'business', 'consulting', 'advisory', 'firm', 'financial', 'insurance', 'logistics', 'b2b'],
            'default_pages': ['Home', 'About Us', 'Services', 'Case Studies', 'Insights', 'Careers', 'Contact'],
            'default_objectives': ['Establish market authority and institutional trust', 'Generate high-value enterprise consultation inquiries'],
            'default_audience': 'C-suite executives, corporate procurement leaders, and business partners',
            'default_functionality': ['Consultation request form', 'Case study portfolio with metric badges', 'Leadership team profiles', 'Downloadable whitepapers'],
            'default_nav': ['Home', 'About', 'Services', 'Case Studies', 'Insights', 'Contact'],
            'default_cta': 'Book Consultation'
        },
        'agency': {
            'label': 'Creative & Marketing Agency Website',
            'keywords': ['agency', 'creative studio', 'marketing', 'advertising', 'branding', 'design agency', 'pr agency', 'digital agency'],
            'default_pages': ['Home', 'Our Work', 'Services', 'Process', 'About Us', 'Contact'],
            'default_objectives': ['Showcase creative excellence and client results', 'Attract ambitious brands for retainer and project engagements'],
            'default_audience': 'Marketing directors, brand founders, and creative leads',
            'default_functionality': ['Visual project portfolio with client case studies', 'Interactive service packages', 'Inquiry questionnaire', 'Client logo ticker'],
            'default_nav': ['Work', 'Services', 'Process', 'About', 'Contact'],
            'default_cta': 'Start a Project'
        },
        'portfolio': {
            'label': 'Portfolio Website',
            'keywords': ['portfolio', 'designer', 'freelancer', 'artist', 'photographer', 'developer', 'showcase', 'personal brand', 'resume'],
            'default_pages': ['Home', 'Selected Work', 'About Me', 'Experience', 'Contact'],
            'default_objectives': ['Highlight personal craftsmanship and creative vision', 'Secure freelance contracts, commissions, or employment offers'],
            'default_audience': 'Design leads, hiring managers, potential clients, and art collectors',
            'default_functionality': ['High-resolution media galleries', 'Case study walk-throughs', 'Downloadable resume / CV', 'Direct contact form'],
            'default_nav': ['Work', 'About', 'Experience', 'Contact'],
            'default_cta': 'Get in Touch'
        },
        'healthcare': {
            'label': 'Healthcare & Medical Website',
            'keywords': ['health', 'healthcare', 'clinic', 'medical', 'hospital', 'doctor', 'physician', 'dentist', 'dental', 'therapy', 'wellness', 'telehealth'],
            'default_pages': ['Home', 'Services & Treatments', 'Our Doctors', 'Patient Information', 'Appointment Booking', 'About Us', 'Contact'],
            'default_objectives': ['Build patient confidence and clinical trust', 'Streamline online appointment bookings and patient inquiries'],
            'default_audience': 'Patients and families seeking trusted medical care and accessible appointments',
            'default_functionality': ['Online appointment scheduling', 'Doctor bios with credentials and specialties', 'Patient portal integration', 'Emergency / location guidance'],
            'default_nav': ['Services', 'Doctors', 'Patient Info', 'About', 'Contact'],
            'default_cta': 'Book Appointment'
        },
        'education': {
            'label': 'Education & E-Learning Website',
            'keywords': ['education', 'school', 'university', 'college', 'academy', 'course', 'courses', 'learning', 'training', 'tutor', 'student', 'bootcamp'],
            'default_pages': ['Home', 'Courses & Programs', 'Admissions', 'Instructors', 'Student Reviews', 'Tuition & Financial Aid', 'Contact'],
            'default_objectives': ['Attract prospective students and drive course enrollments', 'Provide clear curriculum details and academic credentials'],
            'default_audience': 'Prospective students, working professionals upskilling, and parents',
            'default_functionality': ['Course catalog with search and filters', 'Syllabus preview downloads', 'Online enrollment application', 'Student testimonial reviews'],
            'default_nav': ['Courses', 'Admissions', 'Faculty', 'Reviews', 'Contact'],
            'default_cta': 'Enroll Now'
        },
        'restaurant': {
            'label': 'Restaurant & Hospitality Website',
            'keywords': ['restaurant', 'food', 'cafe', 'coffee', 'bakery', 'bistro', 'dining', 'culinary', 'bar', 'catering', 'menu', 'reservations'],
            'default_pages': ['Home', 'Menu', 'About Our Kitchen', 'Table Reservations', 'Private Events', 'Location & Hours', 'Contact'],
            'default_objectives': ['Showcase culinary offerings and atmosphere', 'Drive table reservations and private event inquiries'],
            'default_audience': 'Local diners, food enthusiasts, tourists, and event organizers',
            'default_functionality': ['Interactive dietary-filtered menu', 'Table reservation booking widget', 'Location map & opening hours', 'Private dining inquiry form'],
            'default_nav': ['Menu', 'About', 'Reservations', 'Events', 'Contact'],
            'default_cta': 'Reserve a Table'
        },
        'agriculture': {
            'label': 'Agriculture & Farming Website',
            'keywords': ['agriculture', 'farm', 'farming', 'crops', 'produce', 'agtech', 'harvest', 'organic', 'livestock', 'sustainable agriculture', 'cultivation', 'fertilizer', 'agronomy', 'orchard', 'ranch', 'seed', 'agricultural'],
            'default_pages': ['Home', 'Produce & Crops', 'Farming Practices', 'Sustainability', 'Wholesale', 'About Farm', 'Contact'],
            'default_objectives': ['Connect wholesale buyers and grocery distributors with seasonal crop harvests', 'Highlight sustainable farming practices and organic certifications', 'Facilitate bulk commercial order inquiries'],
            'default_audience': 'Agricultural distributors, retail grocery buyers, food cooperatives, and eco-conscious consumers',
            'default_functionality': ['Crop seasonal harvest calendar', 'Sustainability and organic certification badges', 'Bulk wholesale inquiry form', 'Farm origin and supply chain traceability'],
            'default_nav': ['Produce', 'Farming Practices', 'Sustainability', 'Wholesale', 'About Farm', 'Contact'],
            'default_cta': 'Inquire Wholesale'
        },
        'blog': {
            'label': 'Blog & Editorial Website',
            'keywords': ['blog', 'magazine', 'editorial', 'journal', 'news', 'articles', 'publishing', 'media', 'essays', 'newsletter', 'insights', 'publication', 'content creator'],
            'default_pages': ['Home', 'Trending', 'Categories', 'Featured Stories', 'Authors', 'About', 'Contact'],
            'default_objectives': ['Maximize content readership, article depth, and subscriber retention', 'Deliver organized multi-category browsing with intuitive filtering', 'Grow email newsletter subscription base'],
            'default_audience': 'Inquisitive readers, industry professionals, thought leaders, and subscribers',
            'default_functionality': ['Categorized article feeds with read-time tags', 'Featured editorial hero showcase', 'Author bios and staff picks', 'Instant newsletter subscription banner'],
            'default_nav': ['Trending', 'Categories', 'Stories', 'Authors', 'About', 'Contact'],
            'default_cta': 'Subscribe Now'
        },
        'travel': {
            'label': 'Travel & Hospitality Website',
            'keywords': ['travel', 'tourism', 'hotel', 'resort', 'villa', 'flight', 'flights', 'airline', 'vacation', 'booking', 'tour', 'itinerary', 'destination'],
            'default_pages': ['Home', 'Destinations / Rooms', 'Packages & Deals', 'Experiences & Amenities', 'Booking Engine', 'About Us', 'Contact'],
            'default_objectives': ['Inspire travel desire through immersive visuals', 'Maximize direct booking conversions and guest inquiries'],
            'default_audience': 'Vacationers, luxury travelers, business commuters, and adventure seekers',
            'default_functionality': ['Date-picker search and availability engine', 'Room/flight comparison matrices', 'Customer reviews & trust badges', 'Add-ons & ancillary selection'],
            'default_nav': ['Accommodations', 'Experiences', 'Offers', 'About', 'Contact'],
            'default_cta': 'Book Now'
        },
        'real_estate': {
            'label': 'Real Estate & Property Website',
            'keywords': ['real estate', 'property', 'properties', 'realtor', 'homes', 'apartments', 'rentals', 'commercial real estate', 'mortgage'],
            'default_pages': ['Home', 'Featured Listings', 'Buy', 'Sell', 'Rent', 'Neighborhood Guides', 'Agents', 'Contact'],
            'default_objectives': ['Showcase premier property listings', 'Generate qualified buyer, seller, and tenant leads'],
            'default_audience': 'Homebuyers, property investors, sellers, and prospective tenants',
            'default_functionality': ['Property search with price/bed/bath filters', 'Interactive photo and floorplan gallery', 'Tour booking scheduler', 'Mortgage calculator'],
            'default_nav': ['Listings', 'Buy', 'Sell', 'Agents', 'Contact'],
            'default_cta': 'Schedule a Viewing'
        },
        'sports': {
            'label': 'Sports & Fitness Website',
            'keywords': ['sports', 'tournament', 'league', 'fixtures', 'standings', 'points table', 'live score', 'match results', 'cricket', 'football', 'soccer', 'basketball', 'gym', 'fitness'],
            'default_pages': ['Home', 'Fixtures & Schedule', 'Live Scores', 'Points Table / Standings', 'Teams & Players', 'Match Results', 'Registration', 'Contact'],
            'default_objectives': ['Provide real-time match information and tournament schedules', 'Drive team registrations and fan engagement'],
            'default_audience': 'Players, coaches, team managers, sports fans, and tournament spectators',
            'default_functionality': ['Live scores and fixtures tracker', 'Dynamic points table with rankings', 'Player statistics table', 'Team registration workflow'],
            'default_nav': ['Fixtures', 'Live Scores', 'Standings', 'Teams', 'Results', 'Contact'],
            'default_cta': 'Register Team'
        },
        'media': {
            'label': 'Media, News & Entertainment Website',
            'keywords': ['media', 'news', 'magazine', 'blog', 'podcast', 'movies', 'cinema', 'entertainment', 'editorial', 'journal', 'streaming'],
            'default_pages': ['Home', 'Trending', 'Categories', 'Featured Stories', 'Watchlist / Favorites', 'About', 'Contact'],
            'default_objectives': ['Maximize content readership, streaming engagement, and subscriber retention', 'Deliver organized multi-category media browsing'],
            'default_audience': 'Curious readers, movie buffs, industry followers, and media consumers',
            'default_functionality': ['Category filtering and article search', 'Featured story hero showcase', 'User favorites / watchlist bookmarking', 'Newsletter subscription banner'],
            'default_nav': ['Trending', 'Categories', 'Stories', 'Favorites', 'About'],
            'default_cta': 'Subscribe Now'
        },
        'nonprofit': {
            'label': 'Nonprofit & Community Website',
            'keywords': ['nonprofit', 'charity', 'ngo', 'foundation', 'donation', 'volunteer', 'community', 'mission', 'cause', 'relief', 'advocacy'],
            'default_pages': ['Home', 'Our Mission', 'Programs & Impact', 'Get Involved', 'Stories of Change', 'Donate', 'Contact'],
            'default_objectives': ['Inspire empathy and drive philanthropic donations', 'Recruit volunteers and amplify mission awareness'],
            'default_audience': 'Donors, community volunteers, philanthropic foundations, and supporters',
            'default_functionality': ['Secure one-time and recurring donation form', 'Impact metric counters and stories', 'Volunteer signup form', 'Annual transparency reports'],
            'default_nav': ['Mission', 'Programs', 'Impact', 'Volunteer', 'Contact'],
            'default_cta': 'Donate Today'
        }
    }

    def __init__(self):
        self.last_ai_error: Optional[str] = None

    def extract_category(self, prompt: str, brief_data: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """
        Determines the canonical category code and a professional human-readable website type.
        Prioritizes explicit brief data, followed by prompt intent recognition.
        """
        category_aliases = {
            'corporate': 'business',
            'media': 'blog',
        }

        # 1. Check explicit brief type
        if brief_data and brief_data.get('type'):
            btype = str(brief_data['type']).strip()
            # Check if it matches a known category code or keyword
            btype_lower = btype.lower()
            for cat_id, cat_info in self.CATEGORIES.items():
                if cat_id in btype_lower or any(kw in btype_lower for kw in cat_info['keywords']):
                    norm_cat = category_aliases.get(cat_id, cat_id)
                    return norm_cat, btype
            return 'business', btype

        text = (prompt or '').strip().lower()
        if not text:
            return 'business', 'Business Website'

        # Specific Travel / Flight Booking check
        if 'flight' in text or 'airline' in text:
            return 'travel', 'Flight Booking Website'

        # Score matching keywords across all categories
        best_cat = 'business'
        max_score = 0
        best_label = 'Business Website'

        for cat_id, cat_info in self.CATEGORIES.items():
            score = 0
            for kw in cat_info['keywords']:
                if re.search(r'\b' + re.escape(kw) + r'\b', text):
                    score += 2 if len(kw.split()) > 1 else 1
            if score > max_score:
                max_score = score
                best_cat = cat_id
                best_label = cat_info['label']

        if max_score > 0:
            best_cat = category_aliases.get(best_cat, best_cat)
            # Check if user mentioned an entity name to personalize the type
            m = re.search(r'\b(?:for|named|called)\s+([A-Z][a-zA-Z0-9\s&]+?)(?:\s+website|\s+platform|\s+app|$)', prompt)
            if m:
                brand = m.group(1).strip()
                if len(brand) < 30:
                    return best_cat, f"{best_label} ({brand})"
            return best_cat, best_label

        # Heuristic regex for custom labels
        type_match = re.search(
            r'\b(?:build|create|design|develop|make)\s+(?:an?|the)?\s*([a-z0-9][a-z0-9\s&\-\+]{0,40}?)\s+(website|web site|site|platform|app|system)\b',
            text
        )
        if type_match:
            raw_label = type_match.group(1).strip()
            raw_label = re.sub(r'^(?:a|an|the)\s+', '', raw_label).strip()
            cleaned_label = ' '.join(w.capitalize() for w in raw_label.split())
            suffix = type_match.group(2).lower()
            suffix_clean = 'Platform' if 'platform' in suffix else ('App' if 'app' in suffix else 'Website')
            return 'business', f"{cleaned_label} {suffix_clean}"

        return 'business', 'Business Website'

    def extract_business_objectives(self, prompt: str, brief_data: Optional[Dict[str, Any]] = None, category: str = 'business') -> List[str]:
        """Extracts primary and secondary business goals."""
        goals: List[str] = []
        if brief_data and brief_data.get('goals'):
            raw_goals = brief_data['goals']
            if isinstance(raw_goals, list):
                goals.extend([str(g).strip() for g in raw_goals if str(g).strip()])
            elif isinstance(raw_goals, str):
                goals.extend([g.strip() for g in re.split(r'[,;\n]| and ', raw_goals, flags=re.IGNORECASE) if g.strip()])

        text = prompt or ''
        goal_phrases = [
            r'\b(?:goals?|objectives?|purpose|primary goal)\s*[:\-]\s*([^.\n]+)',
            r'\bwith\s+(?:a\s+)?focus\s+on\s+([^.\n]+)',
            r'\baims?\s+to\s+([^.\n]+)',
            r'\bto\s+enable\s+([^.\n]+)',
            r'\bto\s+create\s+([^.\n]+)',
            r'\bto\s+provide\s+([^.\n]+)',
            r'\bto\s+drive\s+([^.\n]+)',
            r'\bto\s+increase\s+([^.\n]+)',
            r'\bto\s+deliver\s+([^.\n]+)'
        ]
        for pat in goal_phrases:
            for m in re.finditer(pat, text, flags=re.IGNORECASE):
                val = m.group(1).strip()
                if val and len(val) > 4:
                    tokens = [t.strip() for t in re.split(r'[,;\n]| and ', val, flags=re.IGNORECASE) if t.strip()]
                    for t in tokens:
                        if len(t) > 3:
                            goals.append(t)

        # Infill category defaults if none found
        if not goals and category in self.CATEGORIES:
            goals.extend(self.CATEGORIES[category]['default_objectives'])
        elif not goals:
            goals.append('Communicate brand value proposition and drive core user actions')

        # Deduplicate while preserving order
        deduped = []
        seen = set()
        for g in goals:
            k = g.lower()
            if k not in seen:
                seen.add(k)
                deduped.append(g)
        return deduped

    def extract_target_audience(self, prompt: str, brief_data: Optional[Dict[str, Any]] = None, category: str = 'business') -> str:
        """Identifies target audience and user personas."""
        if brief_data and brief_data.get('target_audience'):
            val = brief_data['target_audience']
            return ', '.join(val) if isinstance(val, list) else str(val).strip()

        text = prompt or ''
        audience_patterns = [
            r'\b(?:target\s+audience|audience|target\s+users?|intended\s+for|designed\s+for|built\s+for|aimed\s+at)\s*[:\-]?\s*([^.\n]+)',
            r'\bfor\s+(?:both\s+)?([a-z0-9\s,]+?)\s+(?:looking\s+to|seeking\s+to|who\s+need|who\s+want)\b',
            r'\bhelping\s+([a-z0-9\s,]+?)\s+(?:achieve|reach|find|book|buy)\b'
        ]
        for pat in audience_patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                found = m.group(1).strip()
                if len(found) > 3 and not re.search(r'\b(website|platform|app|pages?)\b', found, flags=re.IGNORECASE):
                    return found

        if category in self.CATEGORIES:
            return self.CATEGORIES[category]['default_audience']
        return 'Prospective clients, decision-makers, and industry partners'

    def extract_design_preferences(self, prompt: str, brief_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extracts visual style, tone of voice, and aesthetic direction."""
        preferences: Dict[str, Any] = {
            'style': 'Modern, Clean',
            'tone': 'Professional',
            'visual_direction': 'High-contrast typography with balanced whitespace and purposeful layouts',
            'color_accents': []
        }

        if brief_data and isinstance(brief_data.get('design_preferences'), dict):
            preferences.update(brief_data['design_preferences'])

        if brief_data and brief_data.get('style'):
            preferences['style'] = str(brief_data['style']).strip()
        if brief_data and brief_data.get('tone'):
            preferences['tone'] = str(brief_data['tone']).strip()

        text = prompt or ''
        # Style detection
        styles = []
        if re.search(r'\bminimal(ist)?\b', text, re.IGNORECASE):
            styles.append('Minimalist')
        if re.search(r'\bmodern\b', text, re.IGNORECASE):
            styles.append('Modern')
        if re.search(r'\bclean\b', text, re.IGNORECASE):
            styles.append('Clean')
        if re.search(r'\bluxur(y|ious)|elegant\b', text, re.IGNORECASE):
            styles.append('Luxury & Elegant')
        if re.search(r'\bdark\s+mode|sleek|futuristic\b', text, re.IGNORECASE):
            styles.append('Dark-Mode Tech')
        if re.search(r'\bplayful|vibrant|colorful\b', text, re.IGNORECASE):
            styles.append('Playful & Vibrant')
        if re.search(r'\bcorporate|enterprise|formal\b', text, re.IGNORECASE):
            styles.append('Corporate & Trustworthy')
        if styles:
            preferences['style'] = ', '.join(dict.fromkeys(styles))

        # Tone detection
        tones = []
        if re.search(r'\bauthoritative|expert|credible\b', text, re.IGNORECASE):
            tones.append('Authoritative & Expert')
        if re.search(r'\bfriendly|warm|approachable\b', text, re.IGNORECASE):
            tones.append('Friendly & Approachable')
        if re.search(r'\binnovative|bold|cutting-edge\b', text, re.IGNORECASE):
            tones.append('Bold & Innovative')
        if re.search(r'\bexclusive|sophisticated|premium\b', text, re.IGNORECASE):
            tones.append('Exclusive & Premium')
        if tones:
            preferences['tone'] = ', '.join(dict.fromkeys(tones))

        # Color cues
        color_patterns = [
            r'\b(?:colors?|palette|accent)\s*[:\-]\s*([^.\n]+)',
            r'\b(monochrome|earth\s+tones|pastel|neon|blue\s+and\s+white|navy|emerald|gold)\b'
        ]
        for pat in color_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                val = m.group(1).strip()
                if val and val.lower() not in [c.lower() for c in preferences['color_accents']]:
                    preferences['color_accents'].append(val)

        return preferences

    def extract_required_functionality(self, prompt: str, brief_data: Optional[Dict[str, Any]] = None, category: str = 'business') -> List[str]:
        """Extracts mandatory interactive features and technical capabilities."""
        features: List[str] = []
        if brief_data and brief_data.get('features'):
            val = brief_data['features']
            if isinstance(val, list):
                features.extend([str(f).strip() for f in val if str(f).strip()])
            elif isinstance(val, str):
                features.extend([f.strip() for f in re.split(r'[,;\n]| and ', val, flags=re.IGNORECASE) if f.strip()])

        text = prompt or ''
        feature_phrases = [
            r'\b(?:features?|functionality|capabilities?)\s*[:\-]\s*([^.\n]+)',
            r'\bincludes?\s+([^.\n]+)',
            r'\bincluding\s+([^.\n]+)',
            r'\bshould\s+(?:include|have|support)\s+([^.\n]+)',
            r'\ballows?\s+(?:users?|visitors?|clients?)\s+to\s+([^.\n]+)',
            r'\busers?\s+can\s+([^.\n]+)',
            r'\bwith\s+a\s+(?:built-in\s+)?([a-z0-9\s\-]+?\s+(?:engine|calculator|form|filter|portal|tool|integration))\b'
        ]
        for pat in feature_phrases:
            for m in re.finditer(pat, text, flags=re.IGNORECASE):
                val = m.group(1).strip()
                if val:
                    # Filter out page list strings mistakenly caught
                    if re.match(r'^(?:pages?|sitemap)\b', val, flags=re.IGNORECASE):
                        continue
                    tokens = [t.strip() for t in re.split(r'[,;/]| and ', val, flags=re.IGNORECASE) if t.strip()]
                    features.extend([t for t in tokens if len(t) > 2 and len(t) < 80])

        if not features and category in self.CATEGORIES:
            features.extend(self.CATEGORIES[category]['default_functionality'])
        elif not features:
            features = ['Responsive navigation bar', 'Interactive contact form', 'Client social proof showcase']

        # Deduplicate
        deduped = []
        seen = set()
        for f in features:
            k = f.lower()
            if k not in seen:
                seen.add(k)
                deduped.append(f)
        return deduped

    def extract_required_pages(self, prompt: str, brief_data: Optional[Dict[str, Any]] = None, category: str = 'business') -> Dict[str, Any]:
        """
        Extracts requested page lists, page counts, and hierarchical structures.
        Supports:
        - Bulleted indentation
        - Path syntax: 'Services > Web Dev > Frontend'
        - Comma-separated page names
        - Explicit page counts: '5-page website'
        """
        text = prompt or ''
        raw_lines = [line.rstrip() for line in re.split(r'[\r\n]+', text) if line.strip()]

        pages_tree: List[Dict[str, Any]] = []
        pages_list: List[str] = []
        page_count: Optional[int] = None

        # Check explicit brief
        if brief_data and brief_data.get('pages_tree') and isinstance(brief_data['pages_tree'], list):
            pages_tree = brief_data['pages_tree']
        elif brief_data and brief_data.get('pages'):
            bpages = brief_data['pages']
            if isinstance(bpages, list):
                if bpages and isinstance(bpages[0], dict) and 'children' in bpages[0]:
                    pages_tree = bpages
                else:
                    pages_list = [str(p).strip() for p in bpages if str(p).strip()]
            elif isinstance(bpages, str):
                pages_list = [p.strip() for p in re.split(r'[,;\n]| and ', bpages, flags=re.IGNORECASE) if p.strip()]

        # Extract page count (e.g., '6 pages' or 'one-page')
        if not page_count:
            if re.search(r'\bone[\s\-]page\b|\bsingle[\s\-]page\b|\blanding\s+page\b', text, re.IGNORECASE):
                page_count = 1
            else:
                count_m = re.search(r'\b(\d+)\s*(?:pages?|page\s+sitemap)\b', text, re.IGNORECASE)
                if count_m:
                    page_count = min(int(count_m.group(1)), 25)

        # Parse bulleted block under Pages: / Sitemap:
        if not pages_tree and not pages_list:
            for idx, line in enumerate(raw_lines):
                if re.match(r'^(?:pages?|page list|sitemap)\s*[:\-]\s*.*$', line, flags=re.IGNORECASE):
                    # Gather subsequent bulleted lines
                    bullets = []
                    for next_line in raw_lines[idx + 1:]:
                        if re.match(r'^\s*(?:[-*•]|\d+[\.\)])\s+', next_line):
                            bullets.append(next_line)
                        else:
                            break
                    if bullets:
                        pages_tree = self._parse_page_tree_from_bullets(bullets)
                    break

        # Parse labeled inline pages (e.g., Pages: Home, About, Services)
        if not pages_tree and not pages_list:
            pages_match = re.search(r'^(?:pages?|page list|sitemap|include pages)\s*[:\-]\s*([^.\n]+)', text, flags=re.IGNORECASE | re.MULTILINE)
            if not pages_match:
                pages_match = re.search(r'\b(?:pages?|sitemap)\s*(?:include|are|should include)?\s*[:\-]\s*([^.\n]+)', text, flags=re.IGNORECASE)
            if pages_match:
                val = pages_match.group(1).strip()
                if '>' in val:
                    pages_tree = self._parse_page_tree_from_paths(val)
                else:
                    tokens = [p.strip() for p in re.split(r'[,;/]| and ', val, flags=re.IGNORECASE) if p.strip()]
                    pages_list = [t for t in tokens if len(t) > 1 and not re.match(r'^\d+$', t)]

        # Look for explicit parent-child mentions like 'Under Services, include Web Design and SEO'
        if not pages_tree:
            subpage_matches = re.finditer(r'\bunder\s+([A-Za-z\s]+?),\s*(?:include|have|add)\s+([^.\n]+)', text, flags=re.IGNORECASE)
            for sm in subpage_matches:
                parent_name = sm.group(1).strip().capitalize()
                children_text = sm.group(2).strip()
                children_list = [c.strip() for c in re.split(r'[,;/]| and ', children_text, flags=re.IGNORECASE) if c.strip()]
                if children_list:
                    if not pages_tree and pages_list:
                        # Convert pages_list into a tree with children under this parent
                        pages_tree = [{'name': p, 'children': []} for p in pages_list]
                    # Find or insert parent
                    parent_node = next((n for n in pages_tree if n['name'].lower() == parent_name.lower()), None)
                    if not parent_node:
                        parent_node = {'name': parent_name, 'children': []}
                        pages_tree.append(parent_node)
                    for c_name in children_list:
                        if not any(ch['name'].lower() == c_name.lower() for ch in parent_node['children']):
                            parent_node['children'].append({'name': c_name, 'children': []})

        # If still no pages found, use category defaults capped by page_count
        if not pages_tree and not pages_list:
            cat_defaults = self.CATEGORIES.get(category, {}).get('default_pages', ['Home', 'About Us', 'Services', 'Contact'])
            if page_count == 1:
                pages_list = ['Home']
            elif page_count:
                pages_list = cat_defaults[:page_count]
            else:
                pages_list = cat_defaults

        # Deduplicate pages_list
        deduped_pages_list: List[str] = []
        seen = set()
        for p in pages_list:
            k = p.lower()
            if k not in seen:
                seen.add(k)
                deduped_pages_list.append(p)

        return {
            'pages_tree': pages_tree,
            'pages_list': deduped_pages_list,
            'page_count': page_count or (len(pages_tree) if pages_tree else len(deduped_pages_list))
        }

    def extract_navigation_requirements(self, prompt: str, brief_data: Optional[Dict[str, Any]], pages: List[str], category: str = 'business') -> Dict[str, Any]:
        """Synthesizes primary navbar links, navbar CTA button, and footer structure."""
        cat_info = self.CATEGORIES.get(category, {})
        default_nav = cat_info.get('default_nav', ['Home', 'Services', 'About', 'Contact'])
        default_cta = cat_info.get('default_cta', 'Get Started')

        # CTA extraction
        cta_match = re.search(r'\b(?:cta|button|call to action|navbar cta)\s*[:\-]\s*["\']?([^.\n"\']+)["\']?', prompt, flags=re.IGNORECASE)
        cta_button = cta_match.group(1).strip() if cta_match else default_cta

        # Primary nav links
        primary_nav = [p for p in pages if p.lower() in [dn.lower() for dn in default_nav]]
        home_page = next((p for p in pages if p.lower() == 'home'), None)
        if home_page and home_page not in primary_nav:
            primary_nav.insert(0, home_page)
        if not primary_nav:
            primary_nav = pages[:5]

        return {
            'primary_nav': primary_nav,
            'cta_button': cta_button,
            'footer_columns': ['Company Info', 'Quick Links', 'Resources', 'Contact & Social']
        }

    def extract_content_requirements(self, prompt: str, brief_data: Optional[Dict[str, Any]], pages: List[str], category: str = 'business') -> Dict[str, Any]:
        """Extracts required content sections and trust proof points."""
        text = prompt or ''
        requirements: List[str] = []

        if re.search(r'\btestimonial|reviews?|social\s+proof\b', text, re.IGNORECASE):
            requirements.append('Customer testimonials and client ratings')
        if re.search(r'\bcase\s+stud(y|ies)|portfolio|work\b', text, re.IGNORECASE):
            requirements.append('Detailed case studies with measurable outcome metrics')
        if re.search(r'\bpricing|plans?|tiers?\b', text, re.IGNORECASE):
            requirements.append('Transparent pricing table with feature comparison')
        if re.search(r'\bfaqs?|frequently\s+asked\b', text, re.IGNORECASE):
            requirements.append('Comprehensive FAQ accordion answering customer questions')
        if re.search(r'\bteam|leadership|founders?\b', text, re.IGNORECASE):
            requirements.append('Executive and team biography cards with credentials')
        if re.search(r'\bpartners?|clients?|trusted\s+by\b', text, re.IGNORECASE):
            requirements.append('Partner & client brand logo banner')

        if not requirements:
            requirements = [
                'High-impact hero with compelling value proposition',
                'Core offerings and feature highlights',
                'Credibility building testimonials and partner trust signals',
                'Frictionless contact and inquiry submission routes'
            ]

        return {
            'editorial_priorities': requirements,
            'required_proof_points': ['Client Testimonials', 'Trust Badges', 'Key Performance Stats']
        }

    def _ai_extract_requirements(self, prompt: str) -> Dict[str, Any]:
        """Calls the AI provider to extract deep requirements from complex prompts."""
        if not config.chat_ai_enabled:
            return {}

        system_instruction = (
            "You are an expert web solution architect. Extract structured project requirements from the prompt. "
            "Output pure JSON matching the requested schema. Do not output markdown or commentary."
        )
        user_message = (
            "Analyze this website prompt and extract:\n"
            "- client: brand or company name (if mentioned, otherwise empty)\n"
            "- category: one of [business, saas, ecommerce, portfolio, agency, healthcare, education, agriculture, blog, restaurant, corporate, travel, real_estate, sports, media, nonprofit]\n"
            "- type: professional website title (e.g. 'Luxury Boutique Hotel Website')\n"
            "- business_objectives: list of 2-3 specific business goals\n"
            "- target_audience: description of the primary audience\n"
            "- design_preferences: object with {style, tone, visual_direction}\n"
            "- required_functionality: list of key features\n"
            "- required_pages: list of page names\n"
            "- navigation_requirements: object with {cta_button, primary_nav}\n\n"
            f"Prompt:\n{prompt}"
        )

        req = CompletionRequest(
            prompt=user_message,
            system_instruction=system_instruction,
            temperature=0.1,
            max_tokens=600,
            response_format={"type": "json_object"},
            timeout_seconds=20
        )
        resp = execute_completion_with_fallback(req)
        if not resp.success:
            self.last_ai_error = resp.error_message
            return {}

        parsed = resp.parse_as_json()
        if isinstance(parsed, dict):
            return parsed
        return {}

    def analyze(self, prompt: str, brief_data: Optional[Dict[str, Any]] = None, ai_enabled: Optional[bool] = None) -> Dict[str, Any]:
        """
        Main analysis pipeline:
        1. Extract heuristic baseline
        2. Enhance with AI extraction if enabled
        3. Merge with explicit user brief updates
        4. Calculate missing fields and confidence score
        """
        self.last_ai_error = None
        text = (prompt or '').strip()

        # Step 1: Heuristic Extraction
        cat_id, web_type = self.extract_category(text, brief_data)
        objectives = self.extract_business_objectives(text, brief_data, cat_id)
        audience = self.extract_target_audience(text, brief_data, cat_id)
        design_prefs = self.extract_design_preferences(text, brief_data)
        functionality = self.extract_required_functionality(text, brief_data, cat_id)
        pages_dict = self.extract_required_pages(text, brief_data, cat_id)

        pages = pages_dict.get('pages_list') or [n['name'] for n in pages_dict.get('pages_tree', [])]
        nav_reqs = self.extract_navigation_requirements(text, brief_data, pages, cat_id)
        content_reqs = self.extract_content_requirements(text, brief_data, pages, cat_id)

        # Client extraction
        client_name = ""
        if brief_data and brief_data.get('client'):
            client_name = str(brief_data['client']).strip()
        else:
            client_match = re.search(r'\b(?:client|company|brand|business|named|called)\s*[:\-]?\s*["\']?([A-Z][a-zA-Z0-9\s&]{1,40}?)["\']?(?:\s+(?:with|for|featuring|website|platform|app)|\.|\n|$)', text)
            if client_match:
                client_name = client_match.group(1).strip()

        # Step 2: AI-Assisted Enrichment if requested and missing key attributes
        should_use_ai = ai_enabled if ai_enabled is not None else config.chat_ai_enabled
        if should_use_ai and len(text) > 20:
            try:
                ai_extracted = self._ai_extract_requirements(text)
                if isinstance(ai_extracted, dict):
                    if not client_name and ai_extracted.get('client'):
                        client_name = str(ai_extracted['client']).strip()
                    if ai_extracted.get('target_audience') and audience == self.CATEGORIES.get(cat_id, {}).get('default_audience'):
                        audience = str(ai_extracted['target_audience']).strip()
                    if ai_extracted.get('business_objectives') and isinstance(ai_extracted['business_objectives'], list):
                        objectives = [str(o).strip() for o in ai_extracted['business_objectives'] if str(o).strip()]
                    if ai_extracted.get('required_functionality') and isinstance(ai_extracted['required_functionality'], list):
                        for f in ai_extracted['required_functionality']:
                            if f not in functionality:
                                functionality.append(str(f).strip())
                    if ai_extracted.get('design_preferences') and isinstance(ai_extracted['design_preferences'], dict):
                        design_prefs.update(ai_extracted['design_preferences'])
            except Exception as e:
                self.last_ai_error = str(e)

        # Step 3: Merge explicit brief_data overrides
        if isinstance(brief_data, dict):
            if brief_data.get('client'):
                client_name = str(brief_data['client']).strip()
            if brief_data.get('type'):
                web_type = str(brief_data['type']).strip()
            if brief_data.get('goals'):
                objectives = [g.strip() for g in str(brief_data['goals']).split(',') if g.strip()]
            if brief_data.get('features'):
                functionality = [f.strip() for f in str(brief_data['features']).split(',') if f.strip()]
            if brief_data.get('style'):
                design_prefs['style'] = str(brief_data['style']).strip()
            if brief_data.get('tone'):
                design_prefs['tone'] = str(brief_data['tone']).strip()

        # Step 4: Missing fields and confidence scoring
        expected_fields = ['client', 'type', 'business_objectives', 'target_audience', 'design_preferences', 'required_functionality', 'required_pages']
        present_count = 0
        missing: List[str] = []

        if client_name:
            present_count += 1
        else:
            missing.append('client')

        if web_type and web_type != 'Business Website':
            present_count += 1
        elif web_type:
            present_count += 0.5
            missing.append('type')

        if objectives and len(objectives) > 0:
            present_count += 1
        else:
            missing.append('goals')

        if audience and audience != self.CATEGORIES.get(cat_id, {}).get('default_audience'):
            present_count += 1
        else:
            missing.append('audience')

        if design_prefs.get('style') and design_prefs['style'] != 'Modern, Clean':
            present_count += 1
        else:
            missing.append('style')

        if functionality and len(functionality) > 1:
            present_count += 1
        else:
            missing.append('features')

        if pages and len(pages) >= 2:
            present_count += 1
        else:
            missing.append('pages')

        confidence = round(min(1.0, max(0.1, present_count / len(expected_fields))), 2)

        # Assemble full result dictionary conforming to BriefContextModel
        res: Dict[str, Any] = {
            'client': client_name,
            'type': web_type,
            'category': cat_id,
            'business_objectives': objectives,
            'target_audience': audience,
            'design_preferences': design_prefs,
            'required_functionality': functionality,
            'required_pages': pages,
            'navigation_requirements': nav_reqs,
            'content_requirements': content_reqs,
            # Legacy compatibility mappings
            'goals': ', '.join(objectives) if objectives else '',
            'services': functionality[:3] if functionality else '',
            'features': ', '.join(functionality) if functionality else '',
            'style': design_prefs.get('style', 'Modern, Clean'),
            'tone': design_prefs.get('tone', 'Professional'),
            'language': 'English',
            'prompt_text': text,
            'missing_fields': missing,
            'confidence': confidence,
            'pages_tree': pages_dict.get('pages_tree', []),
            'pages_list': pages,
            'page_count': pages_dict.get('page_count', len(pages))
        }

        # Travel / Flight domain fields compatibility
        if cat_id == 'travel' and ('flight' in text.lower() or 'airline' in text.lower()):
            res['trip_types'] = 'One-way, Round trip, Multi-city'
            res['passenger_types'] = 'Adult, Child, Infant'
            res['addons'] = 'Seat selection, Extra baggage, In-flight meals, Travel insurance'
            res['payments'] = 'Credit/Debit Cards, UPI, Net Banking, Digital Wallets'
            res['policies'] = 'Cancellation rules, Refund guidelines, Date change fees'

        return res

    def generate_brief_questions(self, prompt: str, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generates dynamic, category-aware clarification questions for missing brief items.
        Returns a list of question objects {id, question, options}.
        """
        cat_id = parsed.get('category', 'business')
        cat_info = self.CATEGORIES.get(cat_id, self.CATEGORIES['corporate'])
        client = parsed.get('client') or 'the website'

        questions = [
            {
                'id': 'type',
                'question': f"What type of website or platform would you like to build for {client}?",
                'options': [
                    cat_info['label'],
                    'Corporate & Business Website',
                    'SaaS Platform Website',
                    'E-commerce Store',
                    'Creative Agency Website',
                    'Portfolio & Showcase'
                ]
            },
            {
                'id': 'audience',
                'question': "Who is your primary target audience or customer base?",
                'options': [
                    cat_info['default_audience'],
                    'B2B Enterprise Decision Makers & Executives',
                    'Tech-savvy consumers and everyday online shoppers',
                    'Working professionals seeking specialized services',
                    'Global travelers and hospitality seekers'
                ]
            },
            {
                'id': 'goals',
                'question': "What is the primary business objective or conversion goal for this website?",
                'options': cat_info['default_objectives'] + [
                    'Maximize lead generation and direct consultation inquiries',
                    'Build brand reputation and showcase institutional credibility',
                    'Drive online transactions and digital product signups'
                ]
            },
            {
                'id': 'features',
                'question': "What key interactive features or tools must be included?",
                'options': cat_info['default_functionality'] + [
                    'Interactive consultation & quote estimator form',
                    'Customer reviews, testimonials, and verified ratings',
                    'Interactive product or service search with facet filters'
                ]
            },
            {
                'id': 'style',
                'question': "What visual style and brand tone best reflect your project vision?",
                'options': [
                    'Modern, Clean, Minimalist (High whitespace, crisp typography)',
                    'Luxury & Sophisticated (Rich dark accents, elegant serifs)',
                    'Bold, Vibrant & Playful (Bright color accents, energetic layout)',
                    'Corporate, Trustworthy & Formal (Navy/slate tones, structured grids)'
                ]
            },
            {
                'id': 'pages',
                'question': "Which core pages should be included in the primary website structure?",
                'options': [
                    ', '.join(cat_info['default_pages'][:5]),
                    'Home, Services, Case Studies, Pricing, About, Contact',
                    'Home, Products, Catalog, About Us, Reviews, FAQ, Contact',
                    'Single-page high-converting landing page with anchored sections'
                ]
            }
        ]

        return questions

    def _parse_page_tree_from_bullets(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Parses indented bullet lists into a hierarchical tree structure."""
        tree: List[Dict[str, Any]] = []
        stack: List[Dict[str, Any]] = []
        indent_stack: List[int] = []

        for raw in lines:
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

    def _parse_page_tree_from_paths(self, value: str) -> List[Dict[str, Any]]:
        """Parses path-like strings like 'Services > Web Dev > Frontend' into a tree."""
        tree: List[Dict[str, Any]] = []
        paths = [p.strip() for p in re.split(r'[;\n]+', value) if p.strip()]

        for path in paths:
            parts = [p.strip() for p in path.split('>') if p.strip()]
            current = tree
            for part in parts:
                existing = next((n for n in current if n['name'].lower() == part.lower()), None)
                if not existing:
                    existing = {'name': part, 'children': []}
                    current.append(existing)
                current = existing['children']

        return tree
