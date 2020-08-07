# Builtins
from typing import Optional
import math
import numpy as np
import argparse

# External modules
import matplotlib.pyplot as plt
from matplotlib import style

# Custom code
from matplotlib.ticker import ScalarFormatter

from Controllers.Database import Database


def show_dashboard(db: Database):
    style.use('fast')
    fig, axes = plt.subplots(2, 3)
    fig.set_size_inches(15, 10)
    fig.set_dpi(100)

    graph2d_from_query(db, axes[0][0], "People per Picture", "Number of People", "Number of Pictures",
                       graph_type="bar")
    graph2d_from_query(db, axes[0][1], "Pictures per Known Person", "Person", "Number of Pictures",
                       graph_type="bar", rotation=30)
    graph2d_from_query(db, axes[0][2], "Picture Counts Over Time", "Date", "Number of Pictures",
                       graph_type="bar", rotation=30)

    graph2d_from_query(db, axes[1][0], "Aperture Frequency", "Aperture", "Number of Pictures",
                       rotation=30, graph_type="bar")

    # Shutter speed is logarithmic so needs to be displayed on a log scale to be readable
    graph2d_from_query(db, axes[1][1], "Shutter Speed Frequency", "Shutter Speed in Seconds", "Number of Pictures")
    axes[1][1].set_xscale("log", base=2)
    axes[1][1].xaxis.set_major_formatter(lambda x, pos: frac_string(x))

    # ISO is logarithmic, bottom weighted, and has accepted values
    isoplot = axes[1][2]
    graph2d_from_query(db, isoplot, "ISO Frequency", "ISO (\"Gain\")", "Number of Pictures")
    isoplot.set_xscale("log", base=2)
    iso_steps = [50 * 2 ** twopow for twopow in range(0, 14)]  # 50, 100, 200, 400, 800...
    biggest_iso = max(isoplot.get_children()[0].get_xdata())
    isoplot.xaxis.set_ticks([step for step in iso_steps if step <= biggest_iso])
    isoplot.xaxis.set_major_formatter(ScalarFormatter())

    fig.tight_layout()  # Reduce figure margins
    plt.show()


def graph2d_from_query(db: Database, plot: plt.axes,
                       title: str, x_label: str, y_label: str,
                       graph_type: str = "plot", rotation: Optional[int] = None):
    # Set up
    plot.set_title(title)
    plot.set_xlabel(x_label)
    plot.set_ylabel(y_label)

    if rotation:
        for label in plot.get_xticklabels():
            label.set_rotation(45)

    sql = queries[title]

    # Get data
    result = db.connection.execute(sql).fetchall()
    pivot = {row["x"]: row["y"] for row in result}

    if graph_type == "plot":
        plot.plot(pivot.keys(), pivot.values())
    elif graph_type == "bar":
        plot.bar(pivot.keys(), pivot.values())
    elif graph_type == "scatter":
        plot.scatter(pivot.keys(), pivot.values())
    else:
        raise Exception("Please specify either 'plot' or 'bar' for graph type.")


# Taken wholesale from https://stackoverflow.com/a/5128558/3915338.
def float_to_fraction(x, error=0.00000001):
    n = int(math.floor(x))
    x -= n
    if x < error:
        return (n, 1)
    elif 1 - error < x:
        return (n + 1, 1)

    # The lower fraction is 0/1
    lower_n = 0
    lower_d = 1
    # The upper fraction is 1/1
    upper_n = 1
    upper_d = 1
    while True:
        # The middle fraction is (lower_n + upper_n) / (lower_d + upper_d)
        middle_n = lower_n + upper_n
        middle_d = lower_d + upper_d
        # If x + error < middle
        if middle_d * (x + error) < middle_n:
            # middle is our new upper
            upper_n = middle_n
            upper_d = middle_d
        # Else If middle < x - error
        elif middle_n < (x - error) * middle_d:
            # middle is our new lower
            lower_n = middle_n
            lower_d = middle_d
        # Else middle is our best fraction
        else:
            return (n * middle_d + middle_n, middle_d)


def frac_string(number_val: float):
    as_fraction = float_to_fraction(number_val)
    return f"{as_fraction[0]}\n--\n{as_fraction[1]}"


# Query storage, to get them out of the way
queries = {}
queries["People per Picture"] = """
    SELECT
        num_people as x,
        count(*) as y
    FROM (
        SELECT
            I.filename,
            count(*) as num_people
        FROM Image I
        INNER JOIN ImageEncoding IE ON I.id = IE.image_id

        GROUP BY I.filename
        ) subquery
    GROUP BY num_people
    """
queries["Pictures per Known Person"] = """
    SELECT
        name as x,
        count(*) as y
    FROM Person P
    INNER JOIN PersonEncoding PE ON P.id = PE.person_id
    GROUP BY name
    ORDER BY name
    """
queries["Picture Counts Over Time"] = """
    SELECT
        (year || '-' || month) as x,
        count(*) as y
    FROM (
        SELECT
            SUBSTR(date_taken, 0, 5) as year,
            SUBSTR(date_taken, 5, 2) as month
        FROM Image 
        WHERE date_taken IS NOT NULL
    ) subquery
    GROUP BY year || '-' || month
    ORDER BY year || '-' || month
"""
queries["Aperture Frequency"] = """
    SELECT
        CASE
            WHEN COALESCE(aperture,0) = 0 THEN 'Unknown'
            ELSE 'f/' || aperture
        END as x,
        num_with as y
    FROM 
        (SELECT
            aperture,
            count(*) as num_with
        FROM Image
        GROUP BY aperture) sq
"""
queries["Shutter Speed Frequency"] = """
SELECT
        COALESCE(shutter_speed,0) as x,
        num_with as y
    FROM 
    (
    SELECT
        shutter_speed,
        count(*) as num_with
    FROM Image
    GROUP BY shutter_speed
    ) sq;
"""
queries["ISO Frequency"] = """
    SELECT
        COALESCE(iso,0) as x,
        num_with as y
    FROM 
        (SELECT
            iso,
            count(*) as num_with
        FROM Image
        GROUP BY iso) sq;
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", help="Path to the database file or where to create it", default="lits.db")
    args = parser.parse_args()
    db = Database(args.db)
    show_dashboard(db)

"""
# Some example data to display
x = np.linspace(0, 2 * np.pi, 400)
y = np.sin(x ** 2)

fig, (ax1, ax2, ax3) = plt.subplots(1, 3)
fig.suptitle('Horizontally stacked subplots')
ax1.plot(x, y)
ax2.plot(x, -y)
ax3.plot(x, z)

print("Interactive:", plt.isinteractive())
plt.show()
print("Done")
"""
