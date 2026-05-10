import asyncio
import json
import time
import sys
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from server.app.core.database import Base
from server.app.models.schemas.chat import ChatResponse
from server.app.models.sql.models import User
from server.app.services.assistant import AssistantService

@dataclass
class EvalResult:
    query: str
    target_topic: str
    eval_type: str = "general"
    detected_route: str = ""
    detected_safety: str = ""
    detected_status: str = ""
    latency_ms: float = 0.0
    sources_found: int = 0
    top_score: float = 0.0
    pass_target_route: bool = False
    pass_target_safety: bool = False
    keyword_match_count: int = 0
    source_match_count: int = 0
    personalization_applied: bool = False
    expected_personalization_applied: bool | None = None
    pass_personalization: bool = True


def build_report_data(results: List[EvalResult]) -> dict:
    total = len(results)
    if total == 0:
        return {
            "summary": {
                "total_samples": 0,
                "route_accuracy": 0.0,
                "safety_accuracy": 0.0,
                "keyword_accuracy": 0.0,
                "source_match_rate": 0.0,
                "grounded_rate": 0.0,
                "personalization_accuracy": 0.0,
                "avg_latency_ms": 0.0,
                "avg_sources_retrieved": 0.0,
                "avg_top_score": 0.0,
            },
            "subset_metrics": {},
            "detailed_results": [],
        }

    passed_routes = sum(1 for r in results if r.pass_target_route)
    passed_safety = sum(1 for r in results if r.pass_target_safety)
    avg_latency = sum(r.latency_ms for r in results) / total
    avg_sources = sum(r.sources_found for r in results) / total
    avg_top_score = sum(r.top_score for r in results) / total
    keyword_accuracy = sum(r.keyword_match_count > 0 for r in results) / total
    source_match_rate = sum(r.source_match_count > 0 for r in results) / total
    grounded_rate = sum(r.detected_status == "grounded" for r in results) / total

    personalization_checks = [r.pass_personalization for r in results if r.expected_personalization_applied is not None]
    personalization_accuracy = sum(personalization_checks) / len(personalization_checks) if personalization_checks else 0.0

    subset_metrics: dict[str, dict[str, float | int]] = {}
    grouped: dict[str, list[EvalResult]] = defaultdict(list)
    for result in results:
        grouped[result.eval_type].append(result)

    for eval_type, items in grouped.items():
        item_total = len(items)
        subset_metrics[eval_type] = {
            "total_samples": item_total,
            "route_accuracy": sum(item.pass_target_route for item in items) / item_total,
            "safety_accuracy": sum(item.pass_target_safety for item in items) / item_total,
            "keyword_accuracy": sum(item.keyword_match_count > 0 for item in items) / item_total,
            "source_match_rate": sum(item.source_match_count > 0 for item in items) / item_total,
            "grounded_rate": sum(item.detected_status == "grounded" for item in items) / item_total,
            "avg_latency_ms": sum(item.latency_ms for item in items) / item_total,
        }

    return {
        "summary": {
            "total_samples": total,
            "route_accuracy": passed_routes / total,
            "safety_accuracy": passed_safety / total,
            "keyword_accuracy": keyword_accuracy,
            "source_match_rate": source_match_rate,
            "grounded_rate": grounded_rate,
            "personalization_accuracy": personalization_accuracy,
            "avg_latency_ms": avg_latency,
            "avg_sources_retrieved": avg_sources,
            "avg_top_score": avg_top_score,
        },
        "subset_metrics": subset_metrics,
        "detailed_results": [vars(r) for r in results],
    }


def write_report(report_data: dict, output_path: Path) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4)

class BaselineEvaluator:
    def __init__(self):
        print("Initializing AssistantService for evaluation...")
        self.service = AssistantService()
        self.dataset_path = Path(__file__).parent / "golden_dataset.json"
        self.db_path = Path(__file__).parent / "baseline_eval.db"
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{self.db_path}", future=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def _prepare_database(self) -> User:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with self.session_factory() as db:
            existing = await db.execute(select(User).where(User.email == "eval@example.com"))
            user = existing.scalar_one_or_none()
            if user is None:
                user = User(email="eval@example.com", hashed_password="hashed")
                db.add(user)
                await db.commit()
                await db.refresh(user)
            return user

    @staticmethod
    def _source_text(sources) -> str:
        return "\n".join(
            " ".join(
                str(part)
                for part in (
                    source.title,
                    source.source,
                    source.topic,
                    source.excerpt,
                    source.source_kind,
                    source.language,
                    source.section,
                )
                if part
            )
            for source in sources
        ).lower()

    async def run(self) -> List[EvalResult]:
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = []
        print(f"Running evaluation on {len(data)} samples...")
        user = await self._prepare_database()

        async with self.session_factory() as db:
            for item in data:
                query = item["query"]
                expected_route = item.get("expected_route")
                expected_safety = item.get("expected_safety")
                expected_contains = [str(value) for value in item.get("expected_contains", [])]
                expected_source_terms = [str(value) for value in item.get("expected_source_terms", [])]
                expected_personalization_applied = item.get("expected_personalization_applied")
                eval_type = str(item.get("eval_type", "general"))
                personalization = item.get("personalization", {})
                intake = item.get("intake", {})
                screening = item.get("screening", {})
                history = item.get("history", [])

                start_time = time.time()
                response: ChatResponse = await self.service.handle_message(
                    message=query,
                    user=user,
                    db=db,
                    intake=intake,
                    screening=screening,
                    history=history,
                    personalization=personalization,
                )
                latency = (time.time() - start_time) * 1000

                sources = response.sources
                top_score = sources[0].score if sources else 0.0
                source_haystack = self._source_text(sources)

                pass_route = True
                if expected_route:
                    pass_route = response.route == expected_route

                pass_safety = True
                if expected_safety:
                    pass_safety = response.safety_mode == expected_safety

                keyword_match_count = 0
                if expected_contains:
                    haystack = f"{response.answer}\n{response.summary}\n{' '.join(source.excerpt for source in sources)}".lower()
                    keyword_match_count = sum(1 for needle in expected_contains if needle.lower() in haystack)

                source_match_count = 0
                if expected_source_terms:
                    source_match_count = sum(1 for needle in expected_source_terms if needle.lower() in source_haystack)

                pass_personalization = True
                if expected_personalization_applied is not None:
                    pass_personalization = response.personalization_applied == bool(expected_personalization_applied)

                res = EvalResult(
                    query=query,
                    target_topic=item["topic"],
                    eval_type=eval_type,
                    detected_route=response.route,
                    detected_safety=response.safety_mode,
                    detected_status=response.status,
                    latency_ms=latency,
                    sources_found=len(sources),
                    top_score=top_score,
                    pass_target_route=pass_route,
                    pass_target_safety=pass_safety,
                    keyword_match_count=keyword_match_count,
                    source_match_count=source_match_count,
                    personalization_applied=response.personalization_applied,
                    expected_personalization_applied=expected_personalization_applied,
                    pass_personalization=pass_personalization,
                )
                results.append(res)
                print(f"Query: {query[:30]}... | Route: {res.detected_route} | Latency: {latency:.2f}ms")

        return results

    def report(self, results: List[EvalResult]):
        report_data = build_report_data(results)
        output_path = Path(__file__).parent / "baseline_report.json"
        write_report(report_data, output_path)
        
        print("\n" + "="*40)
        print("EVALUATION COMPLETE")
        print(f"Route Accuracy: {report_data['summary']['route_accuracy']:.2%}")
        print(f"Safety Accuracy: {report_data['summary']['safety_accuracy']:.2%}")
        print(f"Source Match Rate: {report_data['summary']['source_match_rate']:.2%}")
        print(f"Grounded Rate: {report_data['summary']['grounded_rate']:.2%}")
        print(f"Personalization Accuracy: {report_data['summary']['personalization_accuracy']:.2%}")
        print(f"Avg Latency: {report_data['summary']['avg_latency_ms']:.2f}ms")
        print(f"Avg Top Score: {report_data['summary']['avg_top_score']:.2f}")
        for subset, metrics in report_data.get("subset_metrics", {}).items():
            print(f"- {subset}: route={metrics['route_accuracy']:.2%}, safety={metrics['safety_accuracy']:.2%}, grounded={metrics['grounded_rate']:.2%}")
        print(f"Report saved to: {output_path}")
        print("="*40)

    async def close(self) -> None:
        await self.engine.dispose()

if __name__ == "__main__":
    evaluator = BaselineEvaluator()
    results = asyncio.run(evaluator.run())
    evaluator.report(results)
    asyncio.run(evaluator.close())
