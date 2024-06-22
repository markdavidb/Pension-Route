from customtkinter import *
from harel_pension import HarelPensionScraper
from meitav_pension import MeitavPensionScraper
import time


def main():
    root = CTk()
    root.title("Pension Investment Routes")
    root.geometry("700x400")

    set_appearance_mode("dark")
    set_default_color_theme("dark-blue")

    frame = CTkFrame(master=root)
    frame.pack(pady=30, padx=100, fill="both", expand=True)

    result_label = CTkLabel(
        master=frame,
        width=300,
        height=150,
        text="",
        justify="right",
        anchor="center",
        wraplength=580,
        font=("Arial", 16)
    )
    result_label.pack(pady=10, padx=10, expand=True)

    my_combo = CTkComboBox(master=root, state="readonly", hover=False)
    my_combo.configure(values=["Harel", "Meitav"])
    my_combo.pack(pady=10, padx=10, expand=True)

    def rtl_wrap(text):
        return f'\u202B{text}\u202C'

    def click_handler():
        def clear_label():
            result_label.configure(text="")
            root.update_idletasks()

        def show_loading():
            result_label.configure(text=rtl_wrap("טוען..."))
            root.update_idletasks()

        def scrape_and_display():
            try:
                if my_combo.get() == "Harel":
                    scraper = HarelPensionScraper()
                elif my_combo.get() == "Meitav":
                    scraper = MeitavPensionScraper()
                else:
                    result_label.configure(text=rtl_wrap("Please select a pension provider."))
                    return

                best_route = scraper.scrape()

                # Format the results
                results = f"{best_route.routes_update_date}\n"
                results += f"שם המסלול: {best_route.route_name}\n"
                results += f"תשואה מתחילת שנה: {best_route.rate_2024}\n"
                results += f"תשואה מצטברת 12 חודשים אחרונים: {best_route.rate_12_month}"

                rtl_results = "\n".join(rtl_wrap(line) for line in results.split("\n"))
                result_label.configure(text=rtl_results)
            except Exception as e:
                result_label.configure(text=rtl_wrap(f"An error occurred: {str(e)}"))

        # Schedule the operations
        root.after(0, clear_label)
        root.after(100, show_loading)
        root.after(200, scrape_and_display)

    btn = CTkButton(master=root, text="Scrape", corner_radius=7, fg_color="#313B85", hover_color="#20296C",
                    border_width=1,
                    command=click_handler)

    btn.pack(pady=10, padx=10, expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
