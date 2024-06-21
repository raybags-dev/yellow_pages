from middlewares.errors.error_handler import handle_exceptions
from src.utils.task_utils.loader import emulator
from geopy.geocoders import Nominatim


# Initialize geocoder with a custom user agent
geolocator = Nominatim(user_agent="profiler_user_agent")

# Cache to store fetched zipcodes
zipcode_cache = {}


@handle_exceptions
def reverse_geocode(latitude, longitude):
    location = geolocator.reverse((latitude, longitude), exactly_one=True)
    return location


@handle_exceptions
def assign_zipcode(data, clear_cache=False):
    # Clear the cache if requested
    if clear_cache:
        zipcode_cache.clear()
        print(f"Cache cleared...done! - Calling geo reverse search API...")

    emulator('Fetching zipcodes...', True)

    for obj in data:
        # Check if the object's coordinates are in the cache
        if (obj["latitude"], obj["longitude"]) in zipcode_cache:
            zipcode = zipcode_cache[(obj["latitude"], obj["longitude"])]
            obj['zipcode'] = zipcode
            continue

        if obj:
            print(f' -> Fetching zipcode for (lat={obj["latitude"]}, lon={obj["longitude"]})')
            # Perform reverse geocoding
            location = reverse_geocode(obj['latitude'], obj['longitude'])

            # Extract zipcode from address details
            if location and 'postcode' in location.raw['address']:
                zipcode = location.raw['address']['postcode']
                # Assign zipcode to the object and cache (optional)
                obj['zipcode'] = zipcode
                zipcode_cache[(obj["latitude"], obj["longitude"])] = zipcode

                for key, value in location.raw['address'].items():
                    # Exclude fields
                    if key != 'postcode' and key != 'gender' and key != 'historic' and key != 'man_made':
                        obj[key] = value
            else:
                print(f"Failed to fetch zipcode for ({obj['latitude']}, {obj['longitude']})")

        else:
            print(f"Skipping fetch for object at:\nLatitude: {obj['latitude']} - Longitude: {obj['latitude']}\n")

    emulator('Object ready', False)
    return data

