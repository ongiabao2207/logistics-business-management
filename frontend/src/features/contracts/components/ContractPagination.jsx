import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";

export function ContractPagination({ page, pageSize, totalItems, onPageChange }) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const start = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalItems);
  const nearbyPages = Array.from({ length: totalPages }, (_, index) => index + 1).filter(
    (pageNumber) =>
      pageNumber === 1 ||
      pageNumber === totalPages ||
      Math.abs(pageNumber - page) <= 1,
  );

  return (
    <div className="contract-pagination">
      <span>
        Hiển thị {start}-{end} trên {totalItems} hợp đồng
      </span>
      <div className="contract-page-buttons">
        <button
          type="button"
          disabled={page === 1}
          aria-label="Trang đầu"
          onClick={() => onPageChange(1)}
        >
          <ChevronsLeft size={18} />
        </button>
        <button
          type="button"
          disabled={page === 1}
          aria-label="Trang trước"
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft size={18} />
        </button>
        {nearbyPages.map((pageNumber, index) => {
          const previous = nearbyPages[index - 1];
          const showGap = previous && pageNumber - previous > 1;

          return (
            <span key={pageNumber} className="contract-page-segment">
              {showGap ? <span className="contract-page-gap">...</span> : null}
              <button
                type="button"
                className={pageNumber === page ? "is-active" : ""}
                onClick={() => onPageChange(pageNumber)}
              >
                {pageNumber}
              </button>
            </span>
          );
        })}
        <button
          type="button"
          disabled={page === totalPages}
          aria-label="Trang sau"
          onClick={() => onPageChange(page + 1)}
        >
          <ChevronRight size={18} />
        </button>
        <button
          type="button"
          disabled={page === totalPages}
          aria-label="Trang cuối"
          onClick={() => onPageChange(totalPages)}
        >
          <ChevronsRight size={18} />
        </button>
      </div>
    </div>
  );
}
