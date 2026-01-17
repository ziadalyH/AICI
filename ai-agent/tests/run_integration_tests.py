#!/usr/bin/env python3
"""
Integration Test Runner for RAG System

Runs all test scenarios and generates a detailed report.
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


# Test data
SAMPLE_DRAWING_COMPLIANT = [
    {"type": "POLYLINE", "layer": "Plot Boundary", "points": [[-12000, 10000], [12000, 10000], [12000, 42000], [-12000, 42000]], "closed": True},
    {"type": "POLYLINE", "layer": "Walls", "points": [[-6000, 16000], [6000, 16000], [6000, 32000], [-6000, 32000]], "closed": True},
    {"type": "POLYLINE", "layer": "Extension", "points": [[-4000, 32000], [4000, 32000], [4000, 37000], [-4000, 37000]], "closed": True}  # 5m - COMPLIANT
]

SAMPLE_DRAWING_NON_COMPLIANT = [
    {"type": "POLYLINE", "layer": "Plot Boundary", "points": [[-12000, 10000], [12000, 10000], [12000, 42000], [-12000, 42000]], "closed": True},
    {"type": "POLYLINE", "layer": "Walls", "points": [[-6000, 16000], [6000, 16000], [6000, 32000], [-6000, 32000]], "closed": True},
    {"type": "POLYLINE", "layer": "Extension", "points": [[-4000, 32000], [4000, 32000], [4000, 39000], [-4000, 39000]], "closed": True}  # 7m - NON-COMPLIANT
]


class TestRunner:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.results = []
    
    async def query(self, question: str, objects=None, drawing_updated_at=None, top_k=5):
        """Send query to RAG system."""
        payload = {
            "question": question,
            "drawing_json": objects if objects is not None else {},  # Send empty dict instead of None
            "drawing_updated_at": drawing_updated_at or datetime.utcnow().isoformat() + "Z",
            "top_k": top_k
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/agent/query",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def run_test(self, category: str, test_name: str, question: str, objects=None, expected_checks=None):
        """Run a single test."""
        print(f"\n{'='*80}")
        print(f"🧪 {category} - {test_name}")
        print(f"{'='*80}")
        print(f"❓ Question: {question}")
        
        response = await self.query(question, objects)
        
        if "error" in response:
            print(f"❌ ERROR: {response['error']}")
            self.results.append({
                "category": category,
                "test_name": test_name,
                "question": question,
                "status": "ERROR",
                "error": response["error"]
            })
            return
        
        print(f"\n📊 Answer Type: {response.get('answer_type', 'unknown')}")
        print(f"📝 Answer:\n{response.get('answer', 'No answer')[:500]}...")
        
        # Run checks
        passed = True
        failed_checks = []
        
        if expected_checks:
            for check_name, check_func in expected_checks.items():
                try:
                    if not check_func(response):
                        passed = False
                        failed_checks.append(check_name)
                        print(f"❌ Check failed: {check_name}")
                    else:
                        print(f"✅ Check passed: {check_name}")
                except Exception as e:
                    passed = False
                    failed_checks.append(f"{check_name} (exception: {e})")
                    print(f"❌ Check error: {check_name} - {e}")
        
        status = "PASS" if passed else "FAIL"
        print(f"\n{'✅ PASSED' if passed else '❌ FAILED'}")
        
        self.results.append({
            "category": category,
            "test_name": test_name,
            "question": question,
            "status": status,
            "answer_type": response.get("answer_type"),
            "answer": response.get("answer", "")[:200],
            "failed_checks": failed_checks
        })
    
    async def run_all_tests(self):
        """Run all test scenarios."""
        
        # 1️⃣ Pure Retrieval (PDF only)
        await self.run_test(
            "1️⃣ Pure Retrieval",
            "Permitted Development Rules",
            "What are the permitted development rules for rear extensions?",
            objects=None,
            expected_checks={
                "answer_type_is_pdf": lambda r: r.get("answer_type") == "pdf",
                "mentions_extension": lambda r: "extension" in r.get("answer", "").lower(),
                "has_sources": lambda r: r.get("sources") is not None,
                "no_drawing_timestamp": lambda r: "based on the updated drawing" not in r.get("answer", "").lower()
            }
        )
        
        await self.run_test(
            "1️⃣ Pure Retrieval",
            "Maximum Extension Depth",
            "What is the maximum allowed extension depth?",
            objects=None,
            expected_checks={
                "answer_type_is_pdf": lambda r: r.get("answer_type") == "pdf",
                "contains_number": lambda r: any(c.isdigit() for c in r.get("answer", "")),
                "mentions_metres": lambda r: "m" in r.get("answer", "") or "metre" in r.get("answer", "").lower()
            }
        )
        
        # 2️⃣ Pure JSON Reasoning (Drawing only)
        await self.run_test(
            "2️⃣ Pure JSON Reasoning",
            "Total Plot Area",
            "What is the total plot area?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            expected_checks={
                "mentions_area": lambda r: "768" in r.get("answer", "") or "24" in r.get("answer", ""),
                "mentions_square_metres": lambda r: "m²" in r.get("answer", "") or "square" in r.get("answer", "").lower(),
                "has_drawing_timestamp": lambda r: "based on the updated drawing" in r.get("answer", "").lower()
            }
        )
        
        await self.run_test(
            "2️⃣ Pure JSON Reasoning",
            "Extension Depth",
            "What is the depth of the rear extension?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            expected_checks={
                "mentions_5m": lambda r: "5" in r.get("answer", ""),
                "mentions_metres": lambda r: "m" in r.get("answer", "")
            }
        )
        
        # 3️⃣ Hybrid RAG (PDF + JSON)
        await self.run_test(
            "3️⃣ Hybrid RAG",
            "Building Compliance",
            "Does the building comply with permitted development rules?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            expected_checks={
                "answer_type_is_pdf": lambda r: r.get("answer_type") == "pdf",
                "drawing_context_used": lambda r: r.get("drawing_context_used") is True,
                "mentions_compliance": lambda r: "compliant" in r.get("answer", "").lower() or "comply" in r.get("answer", "").lower()
            }
        )
        
        await self.run_test(
            "3️⃣ Hybrid RAG",
            "Extension Length Check (Non-Compliant)",
            "Is the rear extension longer than allowed?",
            objects=SAMPLE_DRAWING_NON_COMPLIANT,
            expected_checks={
                "mentions_7m": lambda r: "7" in r.get("answer", ""),
                "mentions_6m_limit": lambda r: "6" in r.get("answer", ""),
                "indicates_non_compliance": lambda r: any(word in r.get("answer", "").lower() for word in ["exceed", "longer", "non-compliant", "not compliant"])
            }
        )
        
        # 4️⃣ Session Updates
        print(f"\n{'='*80}")
        print(f"🧪 4️⃣ Session Updates - Drawing Update Detection")
        print(f"{'='*80}")
        
        response1 = await self.query(
            "Is the rear extension compliant?",
            SAMPLE_DRAWING_NON_COMPLIANT,
            "2026-01-17T15:00:00.000Z"
        )
        
        response2 = await self.query(
            "Is the rear extension compliant now?",
            SAMPLE_DRAWING_COMPLIANT,
            "2026-01-17T15:30:00.000Z"
        )
        
        print(f"📝 First Answer (Non-Compliant Drawing):\n{response1.get('answer', '')[:300]}...")
        print(f"\n📝 Second Answer (Compliant Drawing):\n{response2.get('answer', '')[:300]}...")
        
        answers_different = response1.get("answer") != response2.get("answer")
        print(f"\n{'✅' if answers_different else '❌'} Answers are different: {answers_different}")
        
        self.results.append({
            "category": "4️⃣ Session Updates",
            "test_name": "Drawing Update Detection",
            "question": "Is the rear extension compliant? (with update)",
            "status": "PASS" if answers_different else "FAIL",
            "answer_type": response2.get("answer_type"),
            "answer": response2.get("answer", "")[:200]
        })
        
        # 5️⃣ Boundary & Edge Cases
        await self.run_test(
            "5️⃣ Boundary & Edge Cases",
            "Edge Case 6.01m",
            "If the extension is 6.01m deep, is it compliant?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            expected_checks={
                "mentions_6": lambda r: "6" in r.get("answer", ""),
                "indicates_issue": lambda r: any(word in r.get("answer", "").lower() for word in ["exceed", "over", "non-compliant", "limit"])
            }
        )
        
        # 6️⃣ Explainability
        await self.run_test(
            "6️⃣ Explainability",
            "Why Non-Compliant",
            "Why is the building non-compliant?",
            objects=SAMPLE_DRAWING_NON_COMPLIANT,
            expected_checks={
                "provides_reason": lambda r: any(word in r.get("answer", "").lower() for word in ["because", "exceed", "rule", "limit"]),
                "cites_measurements": lambda r: any(c.isdigit() for c in r.get("answer", ""))
            }
        )
        
        # 7️⃣ Negative / Out-of-Scope
        await self.run_test(
            "7️⃣ Negative / Out-of-Scope",
            "Fire Safety (Out of Scope)",
            "What fire safety regulations apply here?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            expected_checks={
                "handles_gracefully": lambda r: r.get("answer_type") == "no_answer" or any(word in r.get("answer", "").lower() for word in ["cannot", "don't", "not"])
            }
        )
        
        # 8️⃣ Instruction Following
        await self.run_test(
            "8️⃣ Instruction Following",
            "Ignore Drawing",
            "Ignore the drawing and answer using the document only: What is the maximum extension depth?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            expected_checks={
                "mentions_general_rule": lambda r: "6" in r.get("answer", "")
            }
        )
        
        # 9️⃣ Agentic / Planning
        await self.run_test(
            "9️⃣ Agentic / Planning",
            "Suggest Compliance Changes",
            "What changes would make this design compliant?",
            objects=SAMPLE_DRAWING_NON_COMPLIANT,
            expected_checks={
                "provides_suggestions": lambda r: any(word in r.get("answer", "").lower() for word in ["reduce", "change", "modify", "adjust", "shorten"]),
                "cites_measurements": lambda r: any(c.isdigit() for c in r.get("answer", ""))
            }
        )
    
    def generate_report(self):
        """Generate test report."""
        print(f"\n\n{'='*80}")
        print(f"📊 TEST REPORT")
        print(f"{'='*80}\n")
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        errors = sum(1 for r in self.results if r["status"] == "ERROR")
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Errors: {errors}")
        print(f"Success Rate: {(passed/total*100):.1f}%\n")
        
        # Group by category
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        for category, tests in categories.items():
            print(f"\n{category}")
            print(f"{'-'*80}")
            for test in tests:
                status_icon = "✅" if test["status"] == "PASS" else "❌" if test["status"] == "FAIL" else "⚠️"
                print(f"{status_icon} {test['test_name']}: {test['status']}")
                if test.get("failed_checks"):
                    print(f"   Failed checks: {', '.join(test['failed_checks'])}")
        
        # Save to file
        report_file = Path("test_report.json")
        with open(report_file, "w") as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "success_rate": passed/total*100
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
    
    async def close(self):
        await self.client.aclose()


async def main():
    """Main test runner."""
    print("🚀 Starting RAG System Integration Tests")
    print(f"Target: http://localhost:8001")
    print(f"Time: {datetime.utcnow().isoformat()}\n")
    
    runner = TestRunner()
    
    try:
        await runner.run_all_tests()
        runner.generate_report()
    finally:
        await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
