import argparse
import importlib.metadata
import json
import time

import litellm


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", required=True)
    parser.add_argument("--fallback", required=True)
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args()

    router = litellm.Router(
        model_list=[
            {
                "model_name": "admission-api-agent",
                "litellm_params": {
                    "model": "openai/admission-primary",
                    "api_base": args.primary,
                    "api_key": "admission-not-a-secret",
                    "timeout": args.timeout,
                },
            },
            {
                "model_name": "admission-fallback",
                "litellm_params": {
                    "model": "openai/admission-fallback",
                    "api_base": args.fallback,
                    "api_key": "admission-not-a-secret",
                    "timeout": args.timeout,
                },
            },
        ],
        fallbacks=[{"admission-api-agent": ["admission-fallback"]}],
        num_retries=0,
        allowed_fails=0,
        cooldown_time=1,
    )

    started = time.monotonic()
    try:
        response = router.completion(
            model="admission-api-agent",
            messages=[{"role": "user", "content": "Milestone 0 fallback probe"}],
        )
        output = {
            "status": "ok",
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": dict(response.usage),
        }
        exit_code = 0
    except Exception as exc:
        output = {
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc)[:800],
        }
        exit_code = 1
    finally:
        router.reset()

    output["elapsed_ms"] = round((time.monotonic() - started) * 1000)
    output["litellm_version"] = importlib.metadata.version("litellm")
    print(json.dumps(output, sort_keys=True))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
