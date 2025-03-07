import requests
from bs4 import BeautifulSoup
import random
import os
import sys


def clear_screen():
    """Clear the terminal screen based on the operating system."""
    try:
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/Mac
            os.system('clear')
    except:
        # If clearing fails, print newlines as a fallback
        print("\n" * 50)


def get_wikipedia_page(query=None, url=None):
    """Get Wikipedia page content either by search query or direct URL."""
    if url:
        full_url = url
    else:
        # Convert query to URL format
        search_query = query.replace(' ', '_')
        full_url = f"https://ru.wikipedia.org/wiki/{search_query}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        response = requests.get(full_url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Ошибка при получении страницы: {response.status_code}")
            return None
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None


def parse_wikipedia_page(html_content):
    """Parse Wikipedia page and extract paragraphs, title, and links."""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Get page title
    title_element = soup.find('h1', id='firstHeading')
    title = title_element.text if title_element else "Неизвестная статья"

    # Get all paragraphs from the main content
    content_div = soup.find('div', class_='mw-parser-output')

    # Debug information
    if not content_div:
        print("Не удалось найти основной контент страницы.")
        input("Нажмите Enter для продолжения...")

    # Get paragraphs directly from the content div
    paragraphs = []
    if content_div:
        # Find all direct paragraph children
        for p in content_div.find_all('p', recursive=False):
            if p.text.strip():
                paragraphs.append(p)

        # If no direct paragraphs, try finding all paragraphs
        if not paragraphs:
            for p in content_div.find_all('p'):
                if p.text.strip():
                    paragraphs.append(p)

    # Extract related links from the hatnotes
    related_links = []
    hatnotes = soup.find_all('div', class_=['hatnote', 'navigation-not-searchable'])
    for hatnote in hatnotes:
        links = hatnote.find_all('a')
        for link in links:
            if link.get('href') and link.get('href').startswith('/wiki/'):
                related_links.append({
                    'title': link.text,
                    'url': 'https://ru.wikipedia.org' + link.get('href')
                })

    # Extract internal links from paragraphs
    internal_links = []
    for p in paragraphs:
        links = p.find_all('a')
        for link in links:
            href = link.get('href')
            if href and href.startswith('/wiki/') and ':' not in href:
                title = link.text.strip()
                if title:  # Only add links with text
                    internal_links.append({
                        'title': title,
                        'url': 'https://ru.wikipedia.org' + href
                    })

    # Remove duplicates while preserving order
    seen_urls = set()
    unique_internal_links = []
    for link in internal_links:
        if link['url'] not in seen_urls and link['title']:
            seen_urls.add(link['url'])
            unique_internal_links.append(link)

    return {
        'title': title,
        'paragraphs': paragraphs,
        'related_links': related_links,
        'internal_links': unique_internal_links[:20]  # Limit to first 20 unique links
    }


def browse_paragraphs(paragraphs, title):
    """Browse through paragraphs of an article."""
    page = 0
    total_pages = len(paragraphs)

    while True:
        clear_screen()
        print(f"Статья: {title} | Параграф {page + 1} из {total_pages}\n")

        # Get the text of the paragraph and handle any HTML entities
        paragraph_text = paragraphs[page].text.strip()
        print(paragraph_text)

        print("\nДействия:")
        print("1. Следующий параграф")
        print("2. Предыдущий параграф")
        print("3. Вернуться к меню статьи")

        choice = input("\nВыберите действие (1-3): ")

        if choice == '1':
            page = (page + 1) % total_pages
        elif choice == '2':
            page = (page - 1) % total_pages
        elif choice == '3':
            return
        else:
            input("Некорректный ввод. Нажмите Enter для продолжения...")


def choose_related_page(related_links):
    """Choose one of the related pages to navigate to."""
    if not related_links:
        print("Связанные страницы не найдены.")
        input("Нажмите Enter для продолжения...")
        return None

    clear_screen()
    print("Связанные страницы:\n")

    for i, link in enumerate(related_links, 1):
        print(f"{i}. {link['title']}")

    print(f"{len(related_links) + 1}. Вернуться к меню статьи")

    while True:
        try:
            choice = input(f"\nВыберите страницу (1-{len(related_links) + 1}): ")
            choice = int(choice)
            if 1 <= choice <= len(related_links):
                return related_links[choice - 1]['url']
            elif choice == len(related_links) + 1:
                return None
            else:
                print("Некорректный ввод.")
                input("Нажмите Enter для продолжения...")
        except ValueError:
            print("Пожалуйста, введите число.")
            input("Нажмите Enter для продолжения...")


def choose_internal_page(internal_links):
    """Choose one of the internal links to navigate to."""
    if not internal_links:
        print("Внутренние ссылки не найдены.")
        input("Нажмите Enter для продолжения...")
        return None

    clear_screen()
    print("Внутренние ссылки:\n")

    for i, link in enumerate(internal_links, 1):
        print(f"{i}. {link['title']}")

    print(f"{len(internal_links) + 1}. Вернуться к меню статьи")

    while True:
        try:
            choice = input(f"\nВыберите страницу (1-{len(internal_links) + 1}): ")
            choice = int(choice)
            if 1 <= choice <= len(internal_links):
                return internal_links[choice - 1]['url']
            elif choice == len(internal_links) + 1:
                return None
            else:
                print("Некорректный ввод.")
                input("Нажмите Enter для продолжения...")
        except ValueError:
            print("Пожалуйста, введите число.")
            input("Нажмите Enter для продолжения...")


def article_menu(parsed_data):
    """Show article menu and process user choices."""
    while True:
        clear_screen()
        print(f"Статья: {parsed_data['title']}\n")
        print("Количество параграфов: {0}".format(len(parsed_data['paragraphs'])))
        print("Количество связанных страниц: {0}".format(len(parsed_data['related_links'])))
        print("Количество внутренних ссылок: {0}".format(len(parsed_data['internal_links'])))
        print("\nДействия:")
        print("1. Листать параграфы текущей статьи")
        print("2. Перейти на одну из связанных страниц")
        print("3. Перейти на одну из внутренних страниц")
        print("4. Выйти из программы")

        choice = input("\nВыберите действие (1-4): ")

        if choice == '1':
            if parsed_data['paragraphs']:
                browse_paragraphs(parsed_data['paragraphs'], parsed_data['title'])
            else:
                print("В статье нет параграфов.")
                input("Нажмите Enter для продолжения...")

        elif choice == '2':
            url = choose_related_page(parsed_data['related_links'])
            if url:
                html_content = get_wikipedia_page(url=url)
                if html_content:
                    parsed_data = parse_wikipedia_page(html_content)

        elif choice == '3':
            url = choose_internal_page(parsed_data['internal_links'])
            if url:
                html_content = get_wikipedia_page(url=url)
                if html_content:
                    parsed_data = parse_wikipedia_page(html_content)

        elif choice == '4':
            print("Выход из программы...")
            sys.exit()

        else:
            print("Некорректный ввод.")
            input("Нажмите Enter для продолжения...")


def main():
    """Main function to run the Wikipedia browser."""
    print("Консольный браузер Википедии\n")

    # Get initial search query
    query = input("Введите поисковый запрос: ")

    # Get and parse the initial Wikipedia page
    html_content = get_wikipedia_page(query=query)
    if html_content:
        parsed_data = parse_wikipedia_page(html_content)
        article_menu(parsed_data)
    else:
        print("Не удалось получить страницу. Проверьте запрос и попробуйте снова.")
        input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()