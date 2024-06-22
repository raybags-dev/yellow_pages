import re
from bs4 import BeautifulSoup
from middlewares.errors.error_handler import handle_exceptions
from src.utils.task_utils.utilities import generate_uuid
from src.utils.logger.logger import custom_logger, initialize_logging


initialize_logging()


@handle_exceptions
def extract_profile_data(page_content):
    if not page_content:
        raise ValueError("Page content is empty! Nothing to process.")
    try:
        soup = BeautifulSoup(page_content, 'html.parser')

        # Extract businessId
        business_id_ele = soup.select_one('div[id="profile"]')
        business_id = business_id_ele.get('data-id') if business_id_ele else None

        # business url
        url_el = soup.select_one('meta[content="4"]')
        url_business = url_el.parent.get('href') if url_el else None
        clean_url = f"https://www.goudengids.nl{url_business}"
        # Correcting the selection of the main container
        main_container = soup.select_one('div#profile .yp-container--lg .lg\\:grid-cols-11')
        if not main_container:
            raise ValueError("Main container not found")

        product_data = {}

        left_container = main_container.select_one('.profile__main')
        if not left_container:
            raise ValueError("Left container not found")

        # Extracting the profile title
        title_element = left_container.select_one('h1[itemprop="name"]')
        profile_title = title_element.text.strip() if title_element else None

        # Extract phone number
        phone_element = left_container.select_one('a[data-ta="PhoneButtonClick"][data-tc="DETAIL"]')
        phone = phone_element.get('href') if phone_element else None
        phone_cleaned = phone.replace('tel:', '') if phone else None

        # Extract address
        full_address = ''
        address_street_ele = left_container.select_one("span[data-yext='street']")
        address_postal_ele = left_container.select_one("span[data-yext='postal-code']")
        address_city_ele = left_container.select_one("span[data-yext='city']")

        address_street = address_street_ele.text.strip() if address_street_ele else None
        address_postcode = address_postal_ele.text.strip() if address_postal_ele else None
        address_city = address_city_ele.text.strip() if address_city_ele else None

        if address_street and address_postcode:
            full_address += f"{address_street}, "
            full_address += address_postcode
            full_address += f" {address_city}"

        # Extract website endpoint
        business_site_ele = left_container.select_one('div[data-ta="WebsiteActionClick"]')
        business_site = business_site_ele.get('data-js-value') if business_site_ele else None

        # Extract business email
        business_email_ele = left_container.select_one('div[data-ta="EmailActionClick"][data-tc="SEARCH"]')
        business_email = business_email_ele.get('data-js-value') if business_email_ele else None

        # =======================================
        # ========= Description =================
        # =======================================
        # Extract the description from the div closest to the input element
        description_ele = soup.select_one('#toggle-box__description + .toggle-box__content')
        description = description_ele.text.strip() if description_ele else None

        # If description is not found, try to get it from the sibling div of the h3 element
        if not description:
            profile_heading_ele = soup.find('h3', class_='tab__title profile-heading')
            if profile_heading_ele:
                description_sibling = profile_heading_ele.find_next_sibling('div', class_='tab__inner')
                if description_sibling:
                    description = description_sibling.text.strip()

        # Extract the meta description as a fallback
        if not description:
            description_alt_ele = soup.find('meta', attrs={'name': 'description'})
            alt_description = description_alt_ele.get('content') if description_alt_ele else None
            description = alt_description

        # Ensure description is a string
        if description is None:
            description = ""
        elif not isinstance(description, str):
            description = str(description)

        # Clean up the description
        if description:
            description = re.sub(r'\s+', ' ', description).strip()

        # Replace specific substrings
        final_description = description.replace('Bel ons.', '').replace('Meer info >>', '').strip()

        # =======================================
        # ========= Extract images =============
        # =======================================
        # Extract images
        all_image_elements = soup.select('div.gallery__column img.gallery__item')
        images = [img.get('src') for img in all_image_elements if img.get('src')]
        business_images = ', '.join(images) if images else None

        # =======================================
        # ========= miscellaneous=============
        # =======================================
        miscellaneous_info = {}
        tab_contents = soup.select('div.tab__content, div#economic-data, div#parking-info')
        for tab in tab_contents:
            tab_heading_ele = tab.select_one('h3.tab__title')
            tab_heading = tab_heading_ele.text.strip() if tab_heading_ele else "Unknown"
            tab_data = []

            if tab.has_attr('id') and tab['id'] == 'economic-data':
                items = tab.select('ul#economic-data-list li')
                for item in items:
                    key = item.select_one('span.font-semibold').text.strip()
                    value = item.contents[-1].strip()
                    tab_data.append({key: value})
            elif tab.has_attr('id') and tab['id'] == 'parking-info':
                items = tab.select('ul#parking-info-list li')
                for item in items:
                    key = item.select_one('span.font-semibold').text.strip()
                    value = item.contents[-1].strip()
                    tab_data.append({key: value})
            elif tab_heading == "Sociale Media":
                social_links = tab.select('div.social-media-wrap a')
                for link in social_links:
                    social_media_name = link['title'].strip()
                    social_media_url = link['href'].strip()
                    tab_data.append({social_media_name: social_media_url})
            elif tab_heading == "Certificeringen":
                items = tab.select('ul.flex.flex-wrap.gap-2 li span')
                for item in items:
                    certification_text = item.text.strip()
                    tab_data.append(certification_text)
            else:
                items = tab.select('div.mb-4.pb-4')
                for item in items:
                    tab_subtitle = item.select_one('span.tab__subtitle').text.strip() if item.select_one(
                        'span.tab__subtitle') else None
                    details = [li.text.strip() for li in item.select('li span')]
                    tab_data.append({tab_subtitle: details})

            miscellaneous_info[tab_heading] = tab_data
            # remove empty list objects
            miscellaneous_info = {k: v for k, v in miscellaneous_info.items() if v != []}

        # =======================================
        # ========= competitor list =============
        # =======================================
        competitors = []
        competitors_list = soup.select('.competitors-list a.competitor')
        base_url = 'https://www.goudengids.nl'
        for competitor in competitors_list:
            competitor_info = {
                'competitor_title': competitor.get('data-title', '').strip().replace('\"', ''),
                'competitor_url': base_url + competitor.get('href', '').strip().replace('\"', '')
            }
            phone = competitor.select_one('.competitor__phone')
            competitor_info['competitor_phone'] = phone.text.strip() if phone else ''
            competitors.append(competitor_info)

        # Debugger line
        custom_logger(f"\n**************\nCollected:\n> url: '{clean_url}'\n> id: '{business_id}'\n> title: '{profile_title}'\n> address: '{full_address}' \n", 'info')

        product_data.update({
            'business_name': profile_title.strip() if profile_title else "unavailable",
            'phone': phone_cleaned.strip() if phone_cleaned else "unavailable",
            'address': full_address.strip() if full_address else "unavailable",
            'business_url': business_site.strip() if business_site else "unavailable",
            'email': business_email.strip() if business_email else "unavailable",
            'business_id': business_id.strip() if business_id else "unavailable",
            'description': final_description.strip() if final_description else "unavailable",
            'business_images': business_images.strip() if business_images else "unavailable",
            'miscellaneous_info': miscellaneous_info if miscellaneous_info else "unavailable",
            'competitors': competitors if competitors else "unavailable",
            'crawled_url': clean_url if clean_url else 'unavailable',
            'uuid': generate_uuid()
        })

        return product_data

    except Exception as e:
        custom_logger(f"Error parsing page content: {e}", log_type="info")
        return {'error': type(e).__name__, 'message': str(e)}
