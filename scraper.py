import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from markdownify import markdownify as md

# Carrega as fontes 
with open("sources.json", "r") as f:
    sources = json.load(f)

def run_scraper():
    with sync_playwright() as p:
        # Lança o navegador 
        browser = p.chromium.launch(headless=True)

        # Timestamp único
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

        for source in sources:
            platform = source["platform"]
            name = source["name"]
            url = source["url"]
            content_selector = source["content_selector"]
            title_selector = source.get("title_selector")

            print(f"Rodando: {platform} - {name}")

            context = None
            html = None

            try:
                # Contexto isolado com locale em português
                context = browser.new_context(locale="pt-BR")
                page = context.new_page()

                # Carrega a página
                page.goto(url, wait_until="domcontentloaded")

                # Aguarda o conteúdo principal
                page.wait_for_selector(content_selector, timeout=20000)

                # Captura o HTML final renderizado
                html = page.content()

            except Exception as e:
                print(f"Erro ao processar {name}: {e}")
                continue

            finally:
                # Fecha o contexto
                if context:
                    context.close()

            # Se não conseguiu capturar HTML, pula
            if not html:
                continue

            # -------------------------
            # Cria estrutura de pastas
            # -------------------------
            os.makedirs(f"snapshots/{platform}", exist_ok=True)
            os.makedirs(f"rendered/{platform}", exist_ok=True)
            os.makedirs(f"versions/{platform}", exist_ok=True)

            # -------------------------
            # 1. SNAPSHOT (HTML bruto)
            # -------------------------
            snapshot_path = f"snapshots/{platform}/{name}_{timestamp}.html"
            with open(snapshot_path, "w", encoding="utf-8") as f:
                f.write(html)

            # -------------------------
            # 2. PROCESSA HTML
            # -------------------------
            soup = BeautifulSoup(html, "html.parser")

            title = soup.select_one(title_selector) if title_selector else None
            content = soup.select_one(content_selector)

            if not content:
                print(f"Aviso: selector '{content_selector}' não encontrado em {name}")
                continue

            # -------------------------
            # 3. RENDERED (HTML limpo)
            # -------------------------
            clean_html = "<div class='document'>"
            if title:
                clean_html += str(title)
            clean_html += str(content)
            clean_html += "</div>"

            rendered_path = f"rendered/{platform}/{name}_{timestamp}.html"
            with open(rendered_path, "w", encoding="utf-8") as f:
                f.write(clean_html)

            # -------------------------
            # 4. VERSION (Markdown)
            # -------------------------
            markdown_content = md(clean_html, heading_style="ATX").strip()

            version_path = f"versions/{platform}/{name}.md"
            with open(version_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            print(f"OK: {name} processado com sucesso.\n")

        browser.close()

if __name__ == "__main__":
    run_scraper()
