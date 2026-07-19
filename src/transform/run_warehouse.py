from ..model.city import CITIES
from .build_clean import rebuild_clean
from .build_warehouse import build_warehouse


def main():
    clean_df = rebuild_clean()

    dim_city, dim_time, fact = build_warehouse(
        clean_df,
        CITIES,
    )

    print(dim_city)
    print(dim_time)
    print(fact)


if __name__ == "__main__":
    main()