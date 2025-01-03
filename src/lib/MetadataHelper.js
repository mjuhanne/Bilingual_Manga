import { deserialize } from '$app/forms';

export async function fetchMetadataFieldVariations(field_name) {
    let body = JSON.stringify({
        'func' : 'get_metadata_field_variations', 
        'param' : {
            'field_name' : field_name,
        }
    });
    const response = await fetch( "/titles", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: body,
    });
    const result = deserialize(await response.text());
    if (!result['success']) {
        return [];
    }
    return result['response']
};
