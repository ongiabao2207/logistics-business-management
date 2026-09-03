/**
 * @typedef {Object} ContractSummary
 * @property {string} contract_id
 * @property {string} customer_name
 * @property {string} valid_from
 * @property {string} valid_to
 * @property {string|number} total_value
 * @property {string} status
 */

/**
 * @typedef {Object} ContractDetailService
 * @property {number} id
 * @property {string} service_name
 * @property {string} service_unit
 * @property {string|number} service_price
 * @property {number} quantity
 */

/**
 * @typedef {ContractSummary & {
 *   payment_terms: string,
 *   updated_at: string,
 *   services: ContractDetailService[],
 * }} ContractDetail
 */
