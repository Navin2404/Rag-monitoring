# src/monitoring/cost_tracker.py
# OpenAI API-ku evlo panam poguthunnu track panrom
# Per token price vachu calculate panrom

# OpenAI Latest Pricing (per 1000 tokens)
PRICING = {
    "gpt-3.5-turbo": {
        "input": 0.0005,  # $0.0005 per 1K input tokens
        "output": 0.0015  # $0.0015 per 1K output tokens
    },
    "llama-3.1-8b-instant": {
        "input": 0.00005, # $0.05 per 1M input
        "output": 0.00008 # $0.08 per 1M output
    },
    "gpt-4": {
        "input": 0.03,
        "output": 0.06
    },
    "gpt-4o": {
        "input": 0.005,
        "output": 0.015
    },
    "gpt-4o-mini": {
        "input": 0.00015,
        "output": 0.0006
    },
    "text-embedding-3-small": {
        "input": 0.00002,  # Embedding cost
        "output": 0.0
    }
}


def calculate_cost(model: str,
                   prompt_tokens: int,
                   completion_tokens: int) -> dict:
    """
    # Token count vachu exact cost calculate panrom
    #
    # Udharanam:
    # prompt_tokens = 500, completion_tokens = 100
    # gpt-3.5-turbo use panna:
    # input cost = (500/1000) * 0.0005 = $0.00025
    # output cost = (100/1000) * 0.0015 = $0.00015
    # total = $0.0004
    """

    if model not in PRICING:
        # Unknown model-ah iruntha 0 return pannu
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": 0.0
        }

    price = PRICING[model]

    # Cost calculate pannu
    input_cost = (prompt_tokens / 1000) * price["input"]
    output_cost = (completion_tokens / 1000) * price["output"]
    total_cost = input_cost + output_cost

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "cost_usd": round(total_cost, 6)  # 6 decimal places
    }


def format_cost_display(cost_usd: float) -> str:
    """
    # Cost-ai readable-ah format panrom
    # $0.000234 → "$0.0002" or "< $0.001"
    """
    if cost_usd < 0.001:
        return f"< $0.001"
    elif cost_usd < 0.01:
        return f"${cost_usd:.4f}"
    else:
        return f"${cost_usd:.3f}"