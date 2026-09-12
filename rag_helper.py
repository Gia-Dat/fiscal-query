import chromadb
from openai import OpenAI
from config import Config

INSTRUCTIONS = """
You are a financial analyst assistant.
Your task is to answer user questions about public companies based strictly on the provided context from SEC filings.

Use only the facts from the context. If the answer cannot be found in the context, respond with:
"I cannot find this information in the provided SEC filings."
""".strip()

PROMPT_TEMPLATE = """
QUESTION: {question}

CONTEXT:
{context}
""".strip()

ENTRY_TEMPLATE = """
Company: {company}
Section: {section}
Content: {text}
""".strip()


class RAGBase:
    def __init__(
        self,
        collection,
        llm_client: OpenAI,
        instructions=INSTRUCTIONS,
        prompt_template=PROMPT_TEMPLATE,
        company="Shopify",
        model="gpt-5.4-mini",
    ):
        self.collection = collection
        self.llm_client = llm_client
        self.instructions = instructions
        self.prompt_template = prompt_template
        self.company = company
        self.model = model

    def search(self, query, num_results=5):
        filter_dict = {"company": self.company} if self.company else None

        results = self.collection.query(
            query_texts=[query],
            n_results=num_results,
            where=filter_dict,
        )
        return results

    def build_context(self, search_results):
        lines = []
        documents = search_results.get("documents", [[]])[0]
        metadatas = search_results.get("metadatas", [[]])[0]

        for text, meta in zip(documents, metadatas):
            entry = ENTRY_TEMPLATE.format(
                company=meta.get("company", "Unknown"),
                section=meta.get("section", "Unknown"),
                text=text,
            )
            lines.append(entry)

        return "\n\n---\n\n".join(lines).strip()

    def build_prompt(self, query, search_results):
        context = self.build_context(search_results)
        return self.prompt_template.format(question=query, context=context)

    def llm(self, prompt):
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.instructions},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content

    def rag(self, query, num_results=5):
        search_results = self.search(query, num_results=num_results)
        prompt = self.build_prompt(query, search_results)
        answer = self.llm(prompt)
        return answer
