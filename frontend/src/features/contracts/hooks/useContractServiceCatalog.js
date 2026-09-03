import { useQuery } from "@tanstack/react-query";

import { priceApi } from "../../prices/api/priceApi";

function isEffectivePriceList(priceList) {
  const today = new Date().toISOString().slice(0, 10);

  return (
    priceList.status === "EFFECTIVE" &&
    priceList.effective_from <= today &&
    priceList.effective_to >= today
  );
}

async function listServicesFromEffectivePriceLists() {
  const priceLists = await priceApi.listPriceLists({ limit: 500 });
  const effectivePriceLists = priceLists.filter(isEffectivePriceList);
  const details = effectivePriceLists.flatMap((priceList) =>
    priceList.details.map((detail) => ({
      priceListId: priceList.id,
      serviceId: detail.service_id,
      unitPrice: detail.unit_price,
    })),
  );
  const uniqueDetails = Array.from(
    new Map(details.map((detail) => [detail.serviceId, detail])).values(),
  );
  const effectiveServices = await Promise.all(
    uniqueDetails.map((detail) => priceApi.getEffectiveServicePrice(detail.serviceId)),
  );

  return effectiveServices.map((service) => ({
    id: service.service_id,
    name: service.service_name,
    unit: service.unit,
    unit_price: service.unit_price,
    price_list_id: service.price_list_id,
    effective_from: service.effective_from,
    effective_to: service.effective_to,
  }));
}

export function useContractServiceCatalog() {
  return useQuery({
    queryKey: ["contracts", "effective-service-catalog"],
    queryFn: listServicesFromEffectivePriceLists,
  });
}
