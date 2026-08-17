import fitz
import httpx
import asyncio

async def test_live():
    # Create sample PDF in memory
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "LUU VAN THANH", fontsize=24)
    page.insert_text((50, 80), "AI ENGINEER | GENERATIVE AI & RAG", fontsize=14)
    page.insert_text((50, 120), "applications. Hands-on experience in LLM integration, real-time conversational AI, RAG pipelines.", fontsize=11)
    
    pdf_bytes = doc.tobytes()
    doc.close()
    
    url = "https://finlegal-document-service-386583671447.asia-southeast1.run.app/extract/file"
    
    print("🚀 Sending test PDF to live Cloud Run service...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        files = {"file": ("CV_AI_LUUVANTHANH.pdf", pdf_bytes, "application/pdf")}
        response = await client.post(url, files=files)
        print("HTTP Status:", response.status_code)
        data = response.json()
        print("\n=== EXTRACTED FULL TEXT FROM CLOUD RUN V6 ===")
        print(data.get("fullText"))
        print("==============================================")
        print("Metadata:", data.get("metadata"))

if __name__ == "__main__":
    asyncio.run(test_live())
