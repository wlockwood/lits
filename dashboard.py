# Builtins
import numpy as np
import argparse

# External modules
import matplotlib.pyplot as plt

# Custom code
from Controllers.Database import Database


def show_dashboard(db: Database):
    fig, axes = plt.subplots(2, 3)
    fig.set_size_inches(15, 10)
    fig.set_dpi(100)

    config_people_per_picture(db, axes[0][0])
    config_pics_per_known(db, axes[0][1])


    plt.show()


def config_people_per_picture(db: Database, plot: plt.axes):
    # Set up
    plot.set_title("People per Picture")

    # Get data
    sql = """
    SELECT
        num_people,
        count(*) pics_with
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
    result = db.connection.execute(sql).fetchall()
    pivot = {row["num_people"]: row["pics_with"] for row in result}
    plot.plot(pivot.keys(), pivot.values())


def config_pics_per_known(db: Database, plot: plt.axes):
    # Set up
    plot.set_title("Known Person Frequency")

    # Get data
    sql = """
    SELECT
        P.name,
        count(*) as num_appeared
    FROM Person P
    INNER JOIN PersonEncoding PE ON P.id = PE.person_id
    GROUP BY P.name
    ORDER BY P.name
    """
    result = db.connection.execute(sql).fetchall()
    pivot = {row["name"]: row["num_appeared"] for row in result}
    plot.bar(pivot.keys(), pivot.values())

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
