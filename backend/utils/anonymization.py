"""
Data anonymization utilities for privacy protection in analytics.

Requirements: 15.5
"""
import hashlib
import logging

logger = logging.getLogger(__name__)


def anonymize_location(latitude, longitude, precision=2):
    """
    Anonymize GPS coordinates by reducing precision.
    
    This function rounds coordinates to a specified number of decimal places,
    creating a geographic area rather than a precise point. This protects
    individual privacy while maintaining useful geographic information for
    analytics.
    
    Precision levels:
    - 0 decimal places: ~111 km accuracy
    - 1 decimal place: ~11 km accuracy
    - 2 decimal places: ~1.1 km accuracy (default)
    - 3 decimal places: ~110 m accuracy
    
    Requirements: 15.5
    
    Args:
        latitude: GPS latitude coordinate
        longitude: GPS longitude coordinate
        precision: Number of decimal places to keep (default: 2)
    
    Returns:
        Tuple of (anonymized_latitude, anonymized_longitude)
    
    Example:
        >>> anonymize_location(40.7128, -74.0060, precision=2)
        (40.71, -74.01)
    """
    try:
        # Round to specified precision
        anon_lat = round(float(latitude), precision)
        anon_lon = round(float(longitude), precision)
        
        return anon_lat, anon_lon
    except (ValueError, TypeError) as e:
        logger.error(f"Error anonymizing location: {e}")
        return None, None


def anonymize_user_id(user_id, salt="grievance_system_salt"):
    """
    Anonymize user ID using one-way hashing.
    
    This creates a consistent anonymous identifier that can be used for
    analytics without revealing the actual user ID. The same user will
    always get the same anonymous ID, allowing for aggregate analysis
    while protecting privacy.
    
    Requirements: 15.5
    
    Args:
        user_id: Original user ID
        salt: Salt value for hashing (should be consistent across application)
    
    Returns:
        Anonymized user ID (SHA-256 hash)
    
    Example:
        >>> anonymize_user_id("user-123")
        "a3f5b8c9d2e1..."
    """
    try:
        # Combine user_id with salt and hash
        combined = f"{user_id}{salt}"
        hashed = hashlib.sha256(combined.encode('utf-8')).hexdigest()
        
        # Return first 16 characters for brevity
        return hashed[:16]
    except Exception as e:
        logger.error(f"Error anonymizing user ID: {e}")
        return None


def anonymize_email(email):
    """
    Anonymize email address by masking most characters.
    
    Keeps the first character and domain, masks the rest.
    
    Requirements: 15.5
    
    Args:
        email: Email address to anonymize
    
    Returns:
        Anonymized email address
    
    Example:
        >>> anonymize_email("john.doe@example.com")
        "j***@example.com"
    """
    try:
        if not email or '@' not in email:
            return "***@***.***"
        
        local, domain = email.split('@', 1)
        
        if len(local) <= 1:
            masked_local = "*"
        else:
            masked_local = local[0] + "***"
        
        return f"{masked_local}@{domain}"
    except Exception as e:
        logger.error(f"Error anonymizing email: {e}")
        return "***@***.***"


def anonymize_phone(phone):
    """
    Anonymize phone number by masking most digits.
    
    Keeps the last 4 digits, masks the rest.
    
    Requirements: 15.5
    
    Args:
        phone: Phone number to anonymize
    
    Returns:
        Anonymized phone number
    
    Example:
        >>> anonymize_phone("1234567890")
        "******7890"
    """
    try:
        if not phone:
            return "***"
        
        # Remove non-digit characters
        digits = ''.join(c for c in phone if c.isdigit())
        
        if len(digits) <= 4:
            return "*" * len(digits)
        
        # Keep last 4 digits
        masked = "*" * (len(digits) - 4) + digits[-4:]
        return masked
    except Exception as e:
        logger.error(f"Error anonymizing phone: {e}")
        return "***"


def anonymize_complaint_for_analytics(complaint_dict):
    """
    Anonymize a complaint dictionary for analytics purposes.
    
    Removes or anonymizes all personally identifiable information (PII)
    while preserving data useful for analytics.
    
    Requirements: 15.5
    
    Args:
        complaint_dict: Dictionary representation of a complaint
    
    Returns:
        Anonymized complaint dictionary
    """
    try:
        # Create a copy to avoid modifying original
        anon_complaint = complaint_dict.copy()
        
        # Anonymize user ID
        if 'user_id' in anon_complaint:
            anon_complaint['user_id'] = anonymize_user_id(anon_complaint['user_id'])
        
        # Anonymize location if present
        if 'location' in anon_complaint and anon_complaint['location']:
            location = anon_complaint['location']
            if 'latitude' in location and 'longitude' in location:
                anon_lat, anon_lon = anonymize_location(
                    location['latitude'],
                    location['longitude'],
                    precision=2
                )
                location['latitude'] = anon_lat
                location['longitude'] = anon_lon
            
            # Remove detailed address, keep only general area
            if 'address' in location:
                # Keep only city/state level information
                address_parts = location['address'].split(',')
                if len(address_parts) > 2:
                    # Keep last 2 parts (typically city and state/country)
                    location['address'] = ', '.join(address_parts[-2:]).strip()
        
        # Remove media URLs (may contain identifying information)
        if 'media_urls' in anon_complaint:
            anon_complaint['media_urls'] = []
        
        # Remove detailed description (may contain PII)
        if 'description' in anon_complaint:
            # Keep only category and keywords for analytics
            anon_complaint['description'] = "[Anonymized for privacy]"
        
        # Keep analytics-relevant fields:
        # - category, priority_level, impact_score, status
        # - created_at, resolved_at (timestamps)
        # - keywords (already processed, no PII)
        # - severity_terms (already processed, no PII)
        
        return anon_complaint
    except Exception as e:
        logger.error(f"Error anonymizing complaint: {e}", exc_info=True)
        return {}


def anonymize_heatmap_data(heatmap_data):
    """
    Anonymize heatmap data for public display.
    
    Reduces location precision and removes any identifying information
    while preserving geographic distribution patterns.
    
    Requirements: 15.5
    
    Args:
        heatmap_data: List of heatmap data points
    
    Returns:
        Anonymized heatmap data
    """
    try:
        anonymized_data = []
        
        for data_point in heatmap_data:
            anon_point = data_point.copy()
            
            # Anonymize location
            if 'location' in anon_point:
                location = anon_point['location']
                if 'latitude' in location and 'longitude' in location:
                    anon_lat, anon_lon = anonymize_location(
                        location['latitude'],
                        location['longitude'],
                        precision=2  # ~1.1 km accuracy
                    )
                    location['latitude'] = anon_lat
                    location['longitude'] = anon_lon
                
                # Generalize address
                if 'address' in location:
                    address_parts = location['address'].split(',')
                    if len(address_parts) > 2:
                        location['address'] = ', '.join(address_parts[-2:]).strip()
            
            # Keep aggregate statistics (counts, averages)
            # These don't contain PII
            
            anonymized_data.append(anon_point)
        
        return anonymized_data
    except Exception as e:
        logger.error(f"Error anonymizing heatmap data: {e}", exc_info=True)
        return []


def remove_pii_from_analytics(analytics_data):
    """
    Remove personally identifiable information from analytics data.
    
    This is a general-purpose function for cleaning any analytics data
    structure of PII before export or display.
    
    Requirements: 15.5
    
    Args:
        analytics_data: Dictionary or list containing analytics data
    
    Returns:
        Cleaned analytics data without PII
    """
    try:
        if isinstance(analytics_data, dict):
            cleaned = {}
            for key, value in analytics_data.items():
                # Skip PII fields
                if key in ['user_id', 'email', 'phone', 'name', 'password_hash', 'address']:
                    if key == 'user_id':
                        cleaned[key] = anonymize_user_id(value)
                    # Skip other PII fields entirely
                    continue
                
                # Recursively clean nested structures
                if isinstance(value, (dict, list)):
                    cleaned[key] = remove_pii_from_analytics(value)
                else:
                    cleaned[key] = value
            
            return cleaned
        
        elif isinstance(analytics_data, list):
            return [remove_pii_from_analytics(item) for item in analytics_data]
        
        else:
            return analytics_data
    
    except Exception as e:
        logger.error(f"Error removing PII from analytics: {e}", exc_info=True)
        return analytics_data
