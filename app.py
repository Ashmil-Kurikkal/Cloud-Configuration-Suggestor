from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from functools import lru_cache
import os
import math

app = Flask(__name__, template_folder='templates')
CORS(app)

# --- Configuration (No changes from previous version) ---
CONFIG = {
    "app_type_mapping": {
        "blog_portfolio": {"workload_pattern": "Stateless Web Tier", "base_ram": 1, "base_vcpu": 1, "suitability_focus": {"web_serving": 1.2, "database": 0.8}},
        "ecommerce": {"workload_pattern": "Stateless Web Tier", "base_ram": 4, "base_vcpu": 2, "suitability_focus": {"web_serving": 1.2, "database": 1.1, "caching": 1.0}},
        "interactive_app": {"workload_pattern": "Memory Intensive", "base_ram": 8, "base_vcpu": 2, "suitability_focus": {"database": 1.2, "caching": 1.1, "web_serving": 0.8}},
        "data_analytics": {"workload_pattern": "Compute Intensive", "base_ram": 8, "base_vcpu": 4, "suitability_focus": {"analytics": 1.5, "database": 0.8}},
        "booking_system": {"workload_pattern": "Memory Intensive", "base_ram": 16, "base_vcpu": 4, "suitability_focus": {"database": 1.5, "caching": 1.0, "web_serving": 0.7}}
    },
    "tag_based_mapping": {
        "ecommerce":      {"tags": ["payments", "search", "user_images", "read_heavy"]},
        "booking_system": {"tags": ["payments", "real_time", "write_heavy", "search"]},
        "interactive_app":{"tags": ["logins", "real_time", "uploads", "write_heavy"]},
        "data_analytics": {"tags": ["datasets", "compute_heavy", "read_heavy"]},
        "blog_portfolio": {"tags": ["text_content", "read_heavy", "uploads"]}
    },
    "traffic_multiplier": {
        "low": {"vcpu": 1.0, "ram": 1.0},
        "medium": {"vcpu": 1.5, "ram": 2.0},
        "high": {"vcpu": 2.5, "ram": 4.0},
        "viral": {"vcpu": 4.0, "ram": 6.0}
    },
    "db_size_ram_bonus": {
        "small": 2,
        "medium": 8,
        "large": 16
    },
    "priority_weights": {
        "cost": {"cost": 1.8, "perf": 0.6},
        "balanced": {"cost": 1.0, "perf": 1.0},
        "performance": {"cost": 0.5, "perf": 1.8}
    }
}

ADDITIONAL_SERVICES = {
    "cdn_storage": {
        "triggers": {"tags": ["user_images", "uploads", "datasets", "text_content"]},
        "title": "Content Delivery & Storage",
        "description": "For applications with significant user uploads or static content, using a dedicated Object Storage service (like AWS S3, Google Cloud Storage) combined with a Content Delivery Network (CDN) is highly recommended. This offloads traffic from your main server, improves global load times, and provides scalable, cost-effective storage.",
        "services": ["AWS S3", "Google Cloud Storage", "Azure Blob Storage", "Cloudflare", "Fastly"]
    },
    "managed_database": {
        "triggers": {"db_size": ["medium", "large"], "tags": ["write_heavy", "read_heavy"]},
        "title": "Managed Database",
        "description": "As your database grows, managing it yourself becomes complex. A managed database service (like AWS RDS, Google Cloud SQL) handles backups, scaling, and maintenance for you, ensuring high availability and durability. This is crucial for business-critical applications.",
        "services": ["AWS RDS", "Google Cloud SQL", "Azure SQL Database", "DigitalOcean Managed Databases"]
    },
    "load_balancer": {
        "triggers": {"traffic": ["high", "viral"]},
        "title": "Load Balancing & Scaling",
        "description": "To handle high or unpredictable traffic, a load balancer distributes incoming requests across multiple server instances. This prevents any single server from being overwhelmed and is the foundation for a high-availability, scalable architecture. Most cloud providers offer managed load balancers and auto-scaling groups.",
        "services": ["AWS ELB", "Google Cloud Load Balancing", "Azure Load Balancer", "Nginx", "HAProxy"]
    },
    "payments": {
        "triggers": {"tags": ["payments"]},
        "title": "Payment Gateway",
        "description": "For e-commerce or any application processing payments, integrating a dedicated payment gateway is essential for security and compliance. These services handle the complexity of credit card processing and fraud detection.",
        "services": ["Stripe", "PayPal", "Braintree", "Adyen"]
    },
     "real_time": {
        "triggers": {"tags": ["real_time"]},
        "title": "Real-time Communication",
        "description": "For applications requiring real-time features like live chat, notifications, or collaborative editing, using a dedicated service can simplify development and ensure scalability.",
        "services": ["Pusher", "Ably", "Firebase Realtime Database"]
    }
}

# --- Database Connection ---
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    db_path = os.path.join(os.path.dirname(__file__), 'instances.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

def query_instances(min_vcpu, min_ram):
    """Queries the database for instances meeting minimum vCPU and RAM requirements."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM instances WHERE vcpu >= ? AND ram >= ?",
        (min_vcpu, min_ram)
    )
    instances = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return instances

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend_api():
    user_needs = request.json
    try:
        recommendations = generate_recommendations(user_needs)
        return jsonify(recommendations)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred. Our engineers have been notified."}), 500

# --- Core Logic ---
def get_analogy_from_tags(user_tags):
    if not user_tags:
        return "blog_portfolio"
    scores = {archetype: len(set(data['tags']) & set(user_tags)) for archetype, data in CONFIG['tag_based_mapping'].items()}
    best_match = max(scores, key=scores.get)
    return best_match if scores[best_match] > 0 else "interactive_app"

def translate_needs_to_requirements(user_needs):
    app_type = user_needs.get('app_type')
    if not app_type:
        raise ValueError("Application type is a required field.")

    final_app_type = get_analogy_from_tags(user_needs.get('custom_tags', [])) if app_type == 'custom' else app_type
    base_specs = CONFIG['app_type_mapping'].get(final_app_type)
    traffic_mult = CONFIG['traffic_multiplier'].get(user_needs.get('traffic', 'low'))
    
    min_vcpu = base_specs['base_vcpu'] * traffic_mult['vcpu']
    min_ram = (base_specs['base_ram'] * traffic_mult['ram']) + CONFIG['db_size_ram_bonus'].get(user_needs.get('db_size', 'small'), 0)

    return {
        'min_vcpu': math.ceil(min_vcpu),
        'min_ram': math.ceil(min_ram),
        'workload_pattern': base_specs['workload_pattern'],
        'suitability_focus': base_specs['suitability_focus'],
        'priority': user_needs.get('priority', 'balanced'),
        'final_app_type': final_app_type,
        'storage_type': user_needs.get('storage_type', 'any'),
        'network_performance': user_needs.get('network_performance', 'any')
    }

def calculate_instance_score(inst, requirements, weights, min_cost, max_cost):
    """
    Calculates a normalized score based on how well an instance fits the requirements.
    A higher score is better.
    """
    # --- 1. Performance Score ---
    # This new logic avoids heavily penalizing "overkill" and rewards it for performance priority.
    cpu_overkill_ratio = inst['vcpu'] / requirements['min_vcpu']
    ram_overkill_ratio = inst['ram'] / requirements['min_ram']

    if weights['perf'] > 1.0:  # Performance priority
        # Reward for more power, with diminishing returns. Capped at a 1.5x bonus.
        cpu_fit_score = min(1.5, 1 + (math.log(cpu_overkill_ratio) / 5))
        ram_fit_score = min(1.5, 1 + (math.log(ram_overkill_ratio) / 5))
    else:  # Balanced or Cost priority
        # Penalize waste gently. A 2x overkill gets ~0.85 score, 4x gets ~0.7.
        cpu_fit_score = max(0.2, 1 - (math.log(cpu_overkill_ratio) / 10))
        ram_fit_score = max(0.2, 1 - (math.log(ram_overkill_ratio) / 10))

    workload_pattern = requirements.get('workload_pattern', 'Stateless Web Tier')
    cpu_weight = 0.4 if 'Memory' in workload_pattern else 0.6
    ram_weight = 0.6 if 'Memory' in workload_pattern else 0.4
    performance_score = (cpu_fit_score * cpu_weight) + (ram_fit_score * ram_weight)

    # --- 2. Suitability Score ---
    # How well this instance's category matches the project's needs.
    category_suitability_score = 0.5
    for focus, weight in requirements['suitability_focus'].items():
        category_suitability_score += (inst.get(focus, 0) * weight) / 4.0
    category_suitability_score = min(category_suitability_score, 1.0)

    # --- 3. Cost Score (Normalized 0-1) ---
    cost_range = max_cost - min_cost
    cost_score = 1.0 if cost_range == 0 else 1 - ((inst['cost_per_month'] - min_cost) / cost_range)

    # --- 4. Final Weighted Score ---
    # The final score is a combination of performance and cost, adjusted by suitability.
    final_score = ((performance_score * weights['perf']) + (cost_score * weights['cost'])) * category_suitability_score
    inst['score'] = final_score
    return inst

def generate_service_suggestions(user_needs, final_app_type):
    suggestions = []
    triggered_services = set()

    user_tags = set(user_needs.get('custom_tags', []))
    # Also include tags from the matched app type
    if final_app_type in CONFIG['tag_based_mapping']:
        user_tags.update(CONFIG['tag_based_mapping'][final_app_type]['tags'])


    for service_key, config in ADDITIONAL_SERVICES.items():
        if service_key in triggered_services:
            continue

        triggered = False
        # Check tag triggers
        if not triggered and 'tags' in config['triggers']:
            if user_tags.intersection(config['triggers']['tags']):
                triggered = True

        # Check db_size triggers
        if not triggered and 'db_size' in config['triggers']:
            if user_needs.get('db_size') in config['triggers']['db_size']:
                triggered = True

        # Check traffic triggers
        if not triggered and 'traffic' in config['triggers']:
            if user_needs.get('traffic') in config['triggers']['traffic']:
                triggered = True

        if triggered:
            suggestions.append({
                "title": config['title'],
                "description": config['description'],
                "services": config['services']
            })
            triggered_services.add(service_key)

    return suggestions

def generate_recommendations(user_needs):
    requirements = translate_needs_to_requirements(user_needs)
    weights = CONFIG['priority_weights'][requirements['priority']]
    
    # Start with all instances that meet the basic CPU and RAM requirements
    base_instances = query_instances(requirements['min_vcpu'], requirements['min_ram'])

    if not base_instances:
        return {"error": "No cloud instances found that match your minimum CPU/RAM requirements. Please try selecting a less demanding project type or scale."}

    # --- Post-Query Filtering for specific tech needs ---
    def is_eligible(inst):
        # Storage Type Filter
        storage_pref = requirements['storage_type']
        inst_storage = inst.get('storage_type', '').lower()
        if storage_pref == 'ssd' and 'ssd' not in inst_storage:
            return False
        if storage_pref == 'nvme_ssd' and 'nvme' not in inst_storage:
            return False
            
        # Network Performance Filter
        network_pref = requirements['network_performance']
        inst_network = inst.get('network_gbps', 0)
        if network_pref == 'medium' and inst_network < 10:
            return False
        if network_pref == 'high' and inst_network < 25:
            return False
            
        return True

    eligible_instances = [inst for inst in base_instances if is_eligible(inst)]

    if not eligible_instances:
        return {"error": "No instances found matching your specific technical criteria (e.g., storage type). Try broadening your search."}

    costs = [inst['cost_per_month'] for inst in eligible_instances]
    min_cost, max_cost = (min(costs), max(costs)) if costs else (0, 0)

    scored_instances = [calculate_instance_score(inst, requirements, weights, min_cost, max_cost) for inst in eligible_instances]
    sorted_instances = sorted(scored_instances, key=lambda x: x['score'], reverse=True)
    
    explanation = f"Based on your project's features, we identified it as a '{requirements['final_app_type'].replace('_', ' ')}' workload, scaled for '{user_needs.get('traffic', 'N/A')}' traffic. Below are all suitable configurations, sorted by our recommendation score."
    
    suggestions = generate_service_suggestions(user_needs, requirements['final_app_type'])

    return {
        "results": sorted_instances,
        "explanation": explanation,
        "suggestions": suggestions
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000)
