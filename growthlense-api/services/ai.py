import os
import json
from openai import OpenAI
from typing import Dict, Any, List

def generate_ai_insights(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates structured e-commerce growth insights including Opportunities, Risks,
    and Recommended Actions based on computed metrics.

    Uses OpenAI API if OPENAI_API_KEY is defined in environments,
    otherwise falls back to a metric-driven local analyst engine.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    
    # If the key is generic or empty, use our high-quality local analyst engine
    if not api_key or api_key.strip() in ["", "YOUR_API_KEY", "default"]:
        return generate_local_analyst_insights(metrics, is_demo=True)

    try:
        client = OpenAI(api_key=api_key)
        
        # Structure the prompt for clean JSON output or parsed segments
        prompt = f"""
        You are GrowthLense AI, an expert e-commerce growth analyst and D2C brand advisor.
        
        Analyze the following computed store metrics:
        {json.dumps(metrics, indent=2)}
        
        Provide high-impact, professional analysis covering:
        1. Three (3) specific growth opportunities.
        2. Three (3) critical risks.
        3. Three (3) immediately actionable recommendations.
        
        Strict Guidelines:
        - Focus on revenue growth, AOV, repeat purchase rates, product popularity, and regional metrics.
        - Every single opportunity, risk, and action must be concise, punchy, and under 40 words.
        - Do not use generic advice. Tailor specifically to the values in the JSON (e.g. mention the top products by name or refer to the specific AOV/Repeat rates).
        
        You must return the response in strict JSON format matching this schema:
        {{
            "opportunities": [
                {{"title": "...", "description": "..."}},
                {{"title": "...", "description": "..."}},
                {{"title": "...", "description": "..."}}
            ],
            "risks": [
                {{"title": "...", "description": "..."}},
                {{"title": "...", "description": "..."}},
                {{"title": "...", "description": "..."}}
            ],
            "actions": [
                {{"title": "...", "description": "..."}},
                {{"title": "...", "description": "..."}},
                {{"title": "...", "description": "..."}}
            ]
        }}
        """

        # Using modern gpt-4o-mini as recommended
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a professional JSON e-commerce analyst. You only output valid JSON matching the requested schema."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        res_text = response.choices[0].message.content
        result = json.loads(res_text)
        result["is_demo"] = False
        return result

    except Exception as e:
        print(f"Error during OpenAI API call: {str(e)}. Falling back to local analyst engine.")
        return generate_local_analyst_insights(metrics, is_demo=True, error_msg=str(e))


def generate_local_analyst_insights(metrics: Dict[str, Any], is_demo: bool = True, error_msg: str = "") -> Dict[str, Any]:
    """
    A smart metric-driven local fallback that provides realistic, highly customized
    insights based on the parsed shop metrics, in case OpenAI keys aren't configured yet.
    """
    revenue = metrics.get("revenue", 0.0)
    orders = metrics.get("orders", 0)
    aov = metrics.get("aov", 0.0)
    repeat_rate = metrics.get("repeat_rate", 0.0)
    top_products = list(metrics.get("top_products", {}).keys())
    
    fav_product = top_products[0] if top_products else "Core Catalog Items"
    second_product = top_products[1] if len(top_products) > 1 else "Standard Bundles"
    
    # 1. GENERATE CUSTOMIZED OPPORTUNITIES
    opportunities = []
    if aov < 50:
        opportunities.append({
            "title": "Low-Ticket Upsell Bundles",
            "description": f"AOV is currently ${aov:.2f}. Create product bundles around '{fav_product}' to push average order value above $60."
        })
    else:
        opportunities.append({
            "title": "High AOV Premium Tiering",
            "description": f"Excellent AOV of ${aov:.2f}. Launch a premium cross-sell widget during cart checkout for your top item '{fav_product}'."
        })
        
    if repeat_rate < 20:
        opportunities.append({
            "title": "Win-Back Email Sequences",
            "description": f"Repeat purchase rate is low ({repeat_rate:.1f}%). Trigger a automated 30-day post-purchase discount code for first-time buyers."
        })
    else:
        opportunities.append({
            "title": "VIP Loyalty Club",
            "description": f"Strong customer retention ({repeat_rate:.1f}%). Build a formal VIP tier giving double points for orders containing '{fav_product}'."
        })

    opportunities.append({
        "title": "Inventory Expansion",
        "description": f"Double down on '{fav_product}' which is driving major revenue. Explore color/size variations to capture latent demand."
    })

    # 2. GENERATE CUSTOMIZED RISKS
    risks = []
    if len(top_products) > 0:
        risks.append({
            "title": "Product Concentration Risk",
            "description": f"'{fav_product}' is a single point of failure. If stock runs out or demand dips, overall revenue will suffer heavily."
        })
    else:
        risks.append({
            "title": "Catalog Underperformance",
            "description": "No products are clearly leading sales volume, indicating generic catalog fatigue across collections."
        })

    if repeat_rate < 15:
        risks.append({
            "title": "High Customer Acquisition Cost (CAC)",
            "description": "Relying purely on one-time buyers. Ad spend is likely unprofitable unless you increase repeat customer frequency."
        })
    else:
        risks.append({
            "title": "Repeat Customer Fatigue",
            "description": f"High repeat rate ({repeat_rate:.1f}%) means loyalists might experience product fatigue. Keep them engaged with fresh releases."
        })

    risks.append({
        "title": "Ad Spend Leakage",
        "description": f"With orders at {orders}, marketing conversion funnels should be audited to ensure traffic isn't bouncing at checkouts."
    })

    # 3. GENERATE CUSTOMIZED ACTIONS
    actions = []
    actions.append({
        "title": f"Bundle '{fav_product}'",
        "description": f"Package '{fav_product}' with '{second_product}' at a 15% discount to lift baseline revenues immediately."
    })
    
    if repeat_rate < 20:
        actions.append({
            "title": "Launch 10% Welcome Flow",
            "description": "Set up a Klaviyo welcome sequence offering 10% off the second purchase to drive repeat rates."
        })
    else:
        actions.append({
            "title": "VIP Referral Bonus",
            "description": "Send a 'Refer a Friend' email campaign to your loyal customer cohort who buy multiple times."
        })

    actions.append({
        "title": "Optimize Mobile Checkout",
        "description": "Enable Apple Pay and Shop Pay to reduce checkout friction and lower cart abandonment rates by 12%."
    })

    return {
        "opportunities": opportunities[:3],
        "risks": risks[:3],
        "actions": actions[:3],
        "is_demo": is_demo,
        "error": error_msg if error_msg else None
    }
