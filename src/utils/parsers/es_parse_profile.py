import re
from bs4 import BeautifulSoup
from middlewares.errors.error_handler import handle_exceptions
from src.utils.task_utils.utilities import generate_uuid
from src.utils.logger.logger import custom_logger, initialize_logging

initialize_logging()


@handle_exceptions
def es_extract_profile_data(page_content):
    if not page_content:
        raise ValueError("Page content is empty! Nothing to process.")
    try:
        soup = BeautifulSoup(page_content, 'html.parser')
        html_content = soup.prettify()

        left_container = soup.select_one('section.data-contact')
        if not left_container:
            custom_logger("Left container not found", 'warn')

        right_container = soup.select_one('section.data-info')
        if not right_container:
            custom_logger("Right container not found", 'warn')

        # =======================================
        # ========= business_id =================
        # =======================================
        canonical_ele = soup.select_one('link[rel="canonical"]')
        pattern = re.compile(r'_(\d+_\d+)\.html')
        if canonical_ele:
            url_value = canonical_ele.get('href')
            match = pattern.search(url_value)
            extracted_id = match.group(1) if match else None
        else:
            extracted_id = None
        # =======================================
        # ========= Business name ===============
        # =======================================
        title_element = left_container.select_one('div.text-center h1[itemprop="name"]')
        sub_title_element = left_container.select_one('div.text-center h1[itemprop="name"] span.localidad')

        sub_title1 = title_element.text.strip() if title_element else None
        sub_title2 = sub_title_element.text.strip() if sub_title_element else None
        profile_title = f"{sub_title1}, {sub_title2}"
        # =======================================
        # ========= Phone ===============
        # =======================================
        phone_element = left_container.select_one('div.detalles-contacto div .content span.telephone b')
        phone = phone_element.text.strip() if phone_element else None
        # =======================================
        # ========= Address ===============
        # =======================================
        full_address = ''
        address_element = left_container.select_one('span.address[itemprop="address"]')
        if address_element:
            address_street = address_element.select_one('span[itemprop="streetAddress"]')
            postcode = address_element.select_one('span[itemprop="postalCode"]')
            city = address_element.select_one('span[itemprop="addressLocality"]')

            address_street = address_street.text.strip() if address_street else ''
            postcode = postcode.text.strip() if postcode else ''
            city = city.text.strip() if city else ''

            full_address = f"{address_street} {postcode} {city}".strip()
        # =======================================
        # ==== Alternative business address  ====
        # =======================================
        alt_bus_add_regexp = r'"businessAddress":"([^"]+)"'
        alt_bus_add_match = re.search(alt_bus_add_regexp, html_content)
        alt_buss_address = alt_bus_add_match.group(1) if alt_bus_add_match else "unavailable"

        # =======================================
        # ========= description =========
        # =======================================
        description_para = right_container.find('p', {'data-yext': 'desc'})
        description_html = description_para.decode_contents() if description_para else "unavailable"
        # Extract text from the description paragraph, preserving line breaks and bold text
        description_text = re.sub(r'<br\s*/?>', '\n', description_html)
        description = re.sub(r'<b>(.*?)</b>', r'**\1**', description_text)
        if description:
            description = re.sub(r'\s+', ' ', description).strip()

        # =======================================
        # ========= Extract images =============
        # =======================================
        # Extract images
        all_image_elements = soup.select('div[id="videos_y_fotos"] div.col-12 div.container img.galeria-imagenes')
        images = [img.get('src') for img in all_image_elements if img.get('src')]
        business_images = ', '.join(images) if images else None

        # =======================================
        # ========= miscellaneous_info =============
        # =======================================
        additionals = soup.select_one('div.info-adicional')
        if additionals:
            # Extract the text from each list item within the element
            list_items = additionals.find_all('li')
            additional_info_list = [li.get_text(strip=True) for li in list_items]
            # Combine the extracted information into a single string
            miscellaneous_info = " | ".join(additional_info_list)
        else:
            miscellaneous_info = ""

        # =======================================
        # ========= local business url =========
        # =======================================
        local_website_element = left_container.select_one('a.sitio-web[rel="noopener nofollow"][itemprop="url"]')
        local_website = local_website_element.get('href') if local_website_element else None

        # =======================================
        # ========= email address ===============
        # =======================================
        email_pattern = r'"customerMail":"([^"]+)"'
        email_match = re.search(email_pattern, html_content)
        email = email_match.group(1) if email_match else None

        phone_pattern_alt = r'"phone":"([^"]+)"'
        phone_match_alt = re.search(phone_pattern_alt, html_content)
        phone_alt = phone_match_alt.group(1) if phone_match_alt else "unavailable"

        # =======================================
        # ========= latitude | longitude =======
        # =======================================
        latitude_regexp = r'"latitude":"([^"]+)"'
        longitude_regexp = r'"longitude":"([^"]+)"'

        latitude_match = re.search(latitude_regexp, html_content)
        longitude_match = re.search(longitude_regexp, html_content)

        latitude = latitude_match.group(1) if latitude_match else "unavailable"
        longitude = longitude_match.group(1) if longitude_match else "unavailable"
        # =======================================
        # ========= profession  =======
        # =======================================
        profession_regexp = r'"activity":"([^"]+)"'
        profession_match = re.search(profession_regexp, html_content)
        profession = profession_match.group(1) if profession_match else "unavailable"

        # =======================================
        # ========= business_url_alt  =======
        # =======================================
        busis_url_alt_regexp = r'"adWebEstablecimiento":"([^"]+)"'
        busis_url_alt_match = re.search(busis_url_alt_regexp, html_content)
        busis_url_alt = busis_url_alt_match.group(1) if busis_url_alt_match else "unavailable"

        product_data = {}

        # Debugger line
        custom_logger(f"\n**************\nCollected:\n> url: '{url_value}'\n> id: '{extracted_id}'\n> title: '{profile_title}'\n> address: '{full_address}' \n", 'info')

        product_data.update({
            'business_id': extracted_id if extracted_id else "unavailable",
            'crawled_url': url_value if url_value else "unavailable",
            'profile_title': profile_title if profile_title else "unavailable",
            'address': full_address if full_address else alt_buss_address,
            'phone': phone if phone else phone_alt,
            'email': email if email else "unavailable",
            'description': description if description else "unavailable",
            'profession': profession if profession else 'null',
            'business_url': local_website if local_website else busis_url_alt,
            'latitude': latitude,
            'longitude': longitude,
            'miscellaneous_info': miscellaneous_info if miscellaneous_info else "unavailable",
            'business_images': business_images if business_images else "unavailbale",
            'uuid': generate_uuid()
        })

        return product_data

    except Exception as e:
        custom_logger(f"Error parsing page content: {e}", log_type="info")
        return {'error': type(e).__name__, 'message': str(e)}
