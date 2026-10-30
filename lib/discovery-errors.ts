// An invalid interest anchor is a record-level limitation, not an empty category,
// quota exhaustion, or a generic malformed-filter response.
export function invalidInterestAnchor(payload:unknown){
 if(!payload||typeof payload!=="object"||!("errors" in payload)||!Array.isArray(payload.errors))return false;
 return payload.errors.some(error=>error&&typeof error==="object"&&error.path==="signal.interests.entities"&&typeof error.message==="string"&&/\ball\b.*\binvalid\b/i.test(error.message));
}
