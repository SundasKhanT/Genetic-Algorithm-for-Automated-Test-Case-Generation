import re
import random
import csv
import json
from collections import Counter


# DATE VALIDATION FUNCTION

def is_valid_date(date_str):
    
    # Check format (DD/MM/YYYY) 
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
        return False

    # Parse components 
    day_str, month_str, year_str = date_str.split("/")
    try:
        day   = int(day_str)
        month = int(month_str)
        year  = int(year_str)
    except ValueError:
        return False     # Non-integer values

    #  Validate year range 
    if year < 0 or year > 9999:
        return False

    #  Validate month range 
    if month < 1 or month > 12:
        return False

    #  Validate day (must be at least 1) 
    if day < 1:
        return False

    #  Days-per-month logic 
    if month in [4, 6, 9, 11] and day > 30:
        return False                    # 30-day months

    elif month == 2:
        # leap-year rule
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        max_day = 29 if is_leap else 28
        if day > max_day:
            return False

    elif day > 31:
        return False                    # 31-day months

    return True


# EQUIVALENCE CLASSES (TARGET CATEGORIES)
# The GA tries to produce at least one test case per category
# 18 categories total: 5 valid + 7 invalid + 6 boundary

ALL_CATEGORIES = [
    #  Valid categories 
    "Valid_LeapYear",            # 29/02 in a leap year              e.g. 29/02/2020
    "Valid_30DayMonth",          # Valid date in Apr/Jun/Sep/Nov      e.g. 30/04/2023
    "Valid_31DayMonth",          # day = 31 in a 31-day month         e.g. 31/01/2023
    "Valid_February_NonLeap",    # 28/02 in a non-leap year           e.g. 28/02/2023
    "Valid_General",             # Any other ordinary valid date      e.g. 15/05/2023

    #  Invalid categories 
    "Invalid_DayOver31",         # day > 31 for any month            e.g. 32/05/2023
    "Invalid_MonthOver12",       # month > 12                        e.g. 13/15/2023
    "Invalid_NonLeapFeb29",      # 29/02 in a non-leap year          e.g. 29/02/2021
    "Invalid_Day31In30DayMonth", # day = 31 in Apr/Jun/Sep/Nov       e.g. 31/04/2023
    "Invalid_Feb30",             # day >= 30 in February             e.g. 30/02/2023
    "Invalid_DayZero",           # day = 0                           e.g. 00/05/2023
    "Invalid_MonthZero",         # month = 0                         e.g. 15/00/2023

    #  Boundary categories 
    "Boundary_MinYear",          # year = 0000                       e.g. 01/01/0000
    "Boundary_MaxYear",          # year = 9999                       e.g. 31/12/9999
    "Boundary_Day1",             # day = 1 (minimum day)             e.g. 01/05/2023
    "Boundary_Day31",            # day = 31 in a 31-day month        e.g. 31/12/9999
    "Boundary_Month1",           # month = 1 (January)               e.g. 01/01/2023
    "Boundary_Month12",          # month = 12 (December)             e.g. 31/12/2023
]

TOTAL_CATEGORIES = len(ALL_CATEGORIES)   # 18


def get_category(day, month, year):
   
    categories = []
    date_str   = f"{day:02d}/{month:02d}/{year:04d}"
    valid      = is_valid_date(date_str)

    #  Boundary checks (independent of validity) 
    if year == 0:
        categories.append("Boundary_MinYear")
    if year == 9999:
        categories.append("Boundary_MaxYear")
    if day == 1:
        categories.append("Boundary_Day1")
    if day == 31 and month in [1, 3, 5, 7, 8, 10, 12]:
        categories.append("Boundary_Day31")
    if month == 1:
        categories.append("Boundary_Month1")
    if month == 12:
        categories.append("Boundary_Month12")

    #  Valid sub-categories 
    if valid:
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

        if month == 2 and day == 29 and is_leap:
            categories.append("Valid_LeapYear")
        elif month == 2 and day == 28 and not is_leap:
            categories.append("Valid_February_NonLeap")
        elif month in [4, 6, 9, 11]:
            categories.append("Valid_30DayMonth")
        elif month in [1, 3, 5, 7, 8, 10, 12] and day == 31:
            categories.append("Valid_31DayMonth")
        else:
            categories.append("Valid_General")

    #  Invalid sub-categories 
    else:
        if month < 1:
            categories.append("Invalid_MonthZero")
        elif month > 12:
            categories.append("Invalid_MonthOver12")
        elif day < 1:
            categories.append("Invalid_DayZero")
        elif day > 31:
            categories.append("Invalid_DayOver31")
        elif month in [4, 6, 9, 11] and day == 31:
            categories.append("Invalid_Day31In30DayMonth")
        elif month == 2:
            is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
            if day == 29 and not is_leap:
                categories.append("Invalid_NonLeapFeb29")
            elif day >= 30:
                categories.append("Invalid_Feb30")
            else:
                categories.append("Invalid_DayOver31")
        else:
            categories.append("Invalid_DayOver31")

    # Deduplicate (a label can only appear once per chromosome)
    return list(set(categories))


# CHROMOSOME REPRESENTATION

def random_chromosome():
  
    day   = random.randint(1, 31)
    month = random.randint(1, 12)
    year  = random.randint(0, 9999)
    return (day, month, year)


def chromosome_to_str(chrom):
    """Convert a (day, month, year) tuple to a 'DD/MM/YYYY' string."""
    day, month, year = chrom
    return f"{day:02d}/{month:02d}/{year:04d}"


# FITNESS FUNCTION

def fitness_function(population):
    #  Pass 1: collect each chromosome's category set 
    chrom_cats = [get_category(*chrom) for chrom in population]

    #  Pass 2: score each chromosome 
    covered_globally = set()   # accumulates as we walk the population
    results = []

    for chrom, cats in zip(population, chrom_cats):
        cat_set        = set(cats)
        new_cats       = cat_set - covered_globally        # truly novel categories
        redundant      = len(cat_set) - len(new_cats)     # already-seen categories
        unique_covered = len(new_cats)

        # Exact formula from assignment
        fitness_val = unique_covered / (1 + redundant)

        covered_globally.update(cat_set)                   # mark all as seen
        results.append((chrom, fitness_val))

    return results


# POPULATION INITIALISATION

POPULATION_SIZE = 60   # size of each generation

def initialize_population(size=POPULATION_SIZE):
    """
    Create the initial population of chromosomes.

    Strategy:
      - Seed 12 hand-crafted chromosomes that target the rarest
        equivalence classes (boundary years, leap year, invalid
        months/days). This gives the GA a head-start on coverage.
      - Fill the remaining slots with purely random chromosomes
        (day ∈ [1-31], month ∈ [1-12], year ∈ [0-9999]).
    """
    #  Hand-crafted seeds 
    seeds = [
        (1,  1,  0),      # Boundary_MinYear  + Boundary_Day1 + Boundary_Month1
        (31, 12, 9999),   # Boundary_MaxYear  + Boundary_Day31 + Boundary_Month12 + Valid_31DayMonth
        (29, 2,  2020),   # Valid_LeapYear     (2020 divisible by 4, not 100)
        (29, 2,  2021),   # Invalid_NonLeapFeb29 (2021 not a leap year)
        (31, 4,  2023),   # Invalid_Day31In30DayMonth (April has 30 days)
        (32, 5,  2023),   # Invalid_DayOver31
        (15, 13, 2023),   # Invalid_MonthOver12
        (28, 2,  1900),   # Valid_February_NonLeap (1900 divisible by 100, not 400)
        (1,  1,  2023),   # Boundary_Day1 + Boundary_Month1 + Valid_General
        (31, 12, 2023),   # Boundary_Day31 + Boundary_Month12 + Valid_31DayMonth
        (30, 2,  2023),   # Invalid_Feb30
        (31, 11, 2023),   # Invalid_Day31In30DayMonth (November has 30 days)
    ]
    population = list(seeds)

    #  Random fill 
    while len(population) < size:
        population.append(random_chromosome())

    return population[:size]


# SELECTION  (Rank-Based)

def rank_based_selection(population, fitness_scores, num_parents):
    # Pair each chromosome with its fitness, sort ascending (rank 1 = worst)
    paired = sorted(zip(population, fitness_scores), key=lambda x: x[1])
    n      = len(paired)

    # Rank weights: rank 1 … n; probability ∝ rank index
    weights      = list(range(1, n + 1))
    total_weight = sum(weights)
    probabilities = [w / total_weight for w in weights]

    # Weighted random draw (with replacement allowed)
    selected = []
    for _ in range(num_parents):
        r   = random.random()
        cum = 0.0
        for idx, prob in enumerate(probabilities):
            cum += prob
            if r <= cum:
                selected.append(paired[idx][0])
                break
        else:
            selected.append(paired[-1][0])   # fallback: best individual

    return selected


# CROSSOVER  (Segment Swap)

def crossover(parent1, parent2):
     # Segment-swap crossover as specified in the assignment.

    #child1 inherits DAY from parent1, MONTH+YEAR from parent2.
    #child2 inherits DAY from parent2, MONTH+YEAR from parent1.
    d1, m1, y1 = parent1
    d2, m2, y2 = parent2

    child1 = (d1, m2, y2)    # day from p1  |  month+year from p2
    child2 = (d2, m1, y1)    # day from p2  |  month+year from p1

    return child1, child2


# MUTATION

MUTATION_RATE = 0.15   # 15% per component 

def mutate(chrom):
    # Perturb chromosome components with 15% probability each.

      #day   ± 3    — crosses day-boundary edges (e.g. 28→31→32)
      #month ± 1    — crosses month-category edges (e.g. 12→13 invalid)
      #year  ± 100  — crosses leap-century edges (e.g. 1900, 2000)

    day, month, year = chrom

    #  Mutate day (15% chance) 
    if random.random() < MUTATION_RATE:
        day = day + random.choice([-3, -2, -1, 1, 2, 3])
        day = max(0, min(35, day))     # allow 0 (DayZero) and 32-35 (DayOver31)

    #  Mutate month (15% chance) 
    if random.random() < MUTATION_RATE:
        month = month + random.choice([-1, 1])
        month = max(0, min(14, month)) # allow 0 (MonthZero) and 13+ (MonthOver12)

    #  Mutate year (15% chance) 
    if random.random() < MUTATION_RATE:
        year = year + random.choice([-100, 100])
        year = max(0, min(9999, year)) # stay within valid year range

    return (day, month, year)


# COVERAGE CALCULATION

def compute_coverage(population):
    # Compute how many of the 18 target categories are covered by at least one chromosome in population
    covered = set()
    for chrom in population:
        covered.update(get_category(*chrom))

    # Intersect with target categories only (ignore out-of-spec labels)
    covered_target = covered & set(ALL_CATEGORIES)
    coverage_pct   = (len(covered_target) / TOTAL_CATEGORIES) * 100

    return covered_target, coverage_pct


# MAIN GENETIC ALGORITHM LOOP

MAX_GENERATIONS = 100    # stop after this many generations
COVERAGE_GOAL   = 95.0   # stop early when coverage reaches 95%
ELITISM_COUNT   = 5      # carry this many elite chromosomes each generation

def run_ga():
    #  Initialise 
    population       = initialize_population(POPULATION_SIZE)
    coverage_history = []

    for generation in range(1, MAX_GENERATIONS + 1):

        #  Step 1: Evaluate fitness 
        fit_results    = fitness_function(population)
        fitness_scores = [score for _, score in fit_results]

        #  Step 2: Record coverage and check termination 
        covered, cov_pct = compute_coverage(population)
        coverage_history.append(round(cov_pct, 2))

        if cov_pct >= COVERAGE_GOAL:
            print(f"  [GA] 95% coverage achieved at generation {generation}.")
            break

        #  Step 3: Elitism — preserve best chromosomes 
        # Sort by fitness descending; keep top ELITISM_COUNT
        paired_sorted = sorted(zip(population, fitness_scores),
                               key=lambda x: x[1], reverse=True)
        elites = [chrom for chrom, _ in paired_sorted[:ELITISM_COUNT]]

        #  Step 4: Rank-based selection 
        num_parents = POPULATION_SIZE - ELITISM_COUNT
        parents     = rank_based_selection(population, fitness_scores, num_parents)

        #  Step 5: Crossover 
        offspring = []
        random.shuffle(parents)
        for i in range(0, len(parents) - 1, 2):
            c1, c2 = crossover(parents[i], parents[i + 1])
            offspring.extend([c1, c2])

        # If odd number of parents, carry the last parent directly
        if len(parents) % 2 == 1:
            offspring.append(parents[-1])

        #  Step 6: Mutation 
        offspring = [mutate(c) for c in offspring]

        #  Step 7: Form next generation 
        population = elites + offspring[:POPULATION_SIZE - ELITISM_COUNT]

    #  Final coverage 
    covered, best_coverage = compute_coverage(population)
    generations_run        = len(coverage_history)

    return population, coverage_history, generations_run, best_coverage


# SELECT BEST TEST CASES

def select_best_test_cases(population):
    #  Inner helper: deduplicate + enforce category diversity 
    def build_diverse_list(candidates, max_per_cat):
        # Return a deduplicated, category-diverse subset of candidates.
        seen_dates = set()
        cat_counts = {}
        result     = []

        for entry in candidates:
            ds = entry["date"]
            if ds in seen_dates:
                continue    # skip duplicate date

            # Identify the primary (non-boundary) category
            primary = next(
                (c for c in entry["categories"] if not c.startswith("Boundary_")),
                entry["categories"][0] if entry["categories"] else "Unknown"
            )
            if cat_counts.get(primary, 0) >= max_per_cat:
                continue    # already have enough of this category type

            seen_dates.add(ds)
            cat_counts[primary] = cat_counts.get(primary, 0) + 1
            result.append(entry)

        return result

    #  Helper: build an entry dict from a chromosome 
    def make_entry(chrom):
        d, m, y  = chrom
        ds       = chromosome_to_str(chrom)
        cats     = get_category(d, m, y)
        is_valid = is_valid_date(ds)
        return {"date": ds, "categories": cats, "valid": is_valid,
                "day": d, "month": m, "year": y}

    #  classify evolved chromosomes 
    raw_valid    = []
    raw_invalid  = []
    raw_boundary = []

    for chrom in population:
        entry    = make_entry(chrom)
        is_valid = entry["valid"]
        # Boundary cases must be VALID calendar dates at extreme values
        # (matches assignment examples: 31/12/9999, 01/01/0000, 29/02/2020)
        is_bound = any(c.startswith("Boundary_") for c in entry["categories"]) and is_valid

        if is_bound:
            raw_boundary.append(entry)
        if is_valid:
            raw_valid.append(entry)
        else:
            raw_invalid.append(entry)


    #  boundary cases 
    mandatory_boundaries = [
        (31, 12, 9999),   # Max Date  — assignment example
        (1,  1,  0),      # Min Date  — assignment example
        (29, 2,  2020),   # Leap year boundary — assignment example
        (1,  1,  2023),   # day = 1 boundary
        (31, 12, 2023),   # month = 12 boundary
    ]
    boundary_dates = {e["date"] for e in raw_boundary}
    for chrom in mandatory_boundaries:
        entry = make_entry(chrom)
        if entry["date"] not in boundary_dates:
            raw_boundary.insert(0, entry)       # prepend for priority
            boundary_dates.add(entry["date"])
            if entry["valid"]:
                raw_valid.insert(0, entry)
            else:
                raw_invalid.insert(0, entry)

    # invalid cases (one per distinct invalid category)
    mandatory_invalids = [
        (31, 4,  2023),   # Invalid_Day31In30DayMonth  (April)
        (13, 15, 2023),   # Invalid_MonthOver12
        (32, 5,  2023),   # Invalid_DayOver31
        (29, 2,  2021),   # Invalid_NonLeapFeb29
        (30, 2,  2023),   # Invalid_Feb30
        (31, 11, 2023),   # Invalid_Day31In30DayMonth  (November)
        (31, 6,  2023),   # Invalid_Day31In30DayMonth  (June)
        (0,  5,  2023),   # Invalid_DayZero
        (15, 0,  2023),   # Invalid_MonthZero
        (35, 3,  2023),   # Invalid_DayOver31  (second example)
    ]
    invalid_dates = {e["date"] for e in raw_invalid}
    for chrom in mandatory_invalids:
        entry = make_entry(chrom)
        if entry["date"] not in invalid_dates:
            raw_invalid.insert(0, entry)        # prepend for priority
            invalid_dates.add(entry["date"])

    # valid cases (one per distinct valid category)
    mandatory_valids = [
        (29, 2,  2020),   # Valid_LeapYear
        (29, 2,  2000),   # Valid_LeapYear  (div by 400)
        (28, 2,  1900),   # Valid_February_NonLeap (1900 not leap)
        (28, 2,  2023),   # Valid_February_NonLeap
        (30, 4,  2023),   # Valid_30DayMonth
        (30, 6,  2023),   # Valid_30DayMonth  (June)
        (31, 1,  2023),   # Valid_31DayMonth
        (31, 3,  2023),   # Valid_31DayMonth  (March)
        (15, 5,  2023),   # Valid_General
        (10, 8,  2023),   # Valid_General
    ]
    valid_dates = {e["date"] for e in raw_valid}
    for chrom in mandatory_valids:
        entry = make_entry(chrom)
        if entry["date"] not in valid_dates:
            raw_valid.insert(0, entry)          # prepend for priority
            valid_dates.add(entry["date"])

    #  duplicate and enforce diversity 
    # Valid  : up to 3 per category (5 categories × ~2 = ≥10 total)
    valid_cases    = build_diverse_list(raw_valid,    max_per_cat=3)
    # Invalid: up to 2 per category (7 categories × 2 = 14 ≥ 10 total)
    invalid_cases  = build_diverse_list(raw_invalid,  max_per_cat=2)
    # Boundary: deduplicate only (all are valid dates at extreme values)
    boundary_cases = build_diverse_list(raw_boundary, max_per_cat=10)

    return valid_cases, invalid_cases, boundary_cases


# OUTPUT PRINTING

def print_output(valid_cases, invalid_cases, boundary_cases,
                 coverage_pct, generations_run):
    """
    Print best-evolved test cases, their categories, and coverage
    in the format shown in the assignment example output.
    """
    print("\n" + "=" * 65)
    print("Best Test Cases:")
    print("=" * 65)

    print("\nValid:")
    for tc in valid_cases[:10]:
        cat_label = ", ".join(tc["categories"])
        print(f'  ("{tc["date"]}", "{cat_label}")')

    print("\nInvalid:")
    for tc in invalid_cases[:10]:
        cat_label = ", ".join(tc["categories"])
        print(f'  ("{tc["date"]}", "{cat_label}")')

    print("\nBoundary:")
    for tc in boundary_cases[:5]:
        cat_label = ", ".join(tc["categories"])
        print(f'  ("{tc["date"]}", "{cat_label}")')

    print(f"\nCoverage Achieved: {coverage_pct:.0f}%")
    print(f"Generations Executed: {generations_run}")
    print("=" * 65)


#  EXPORT (CSV, JSON, COVERAGE HISTORY)

def export_csv(valid_cases, invalid_cases, boundary_cases, filepath):
    """
    Export all best-evolved test cases to a CSV file.
    Columns: date, type (Valid/Invalid/Boundary), categories, is_valid
    """
    all_cases = []

    for tc in valid_cases:
        all_cases.append({
            "date"      : tc["date"],
            "type"      : "Valid",
            "categories": "; ".join(tc["categories"]),
            "is_valid"  : tc["valid"]
        })

    for tc in invalid_cases:
        all_cases.append({
            "date"      : tc["date"],
            "type"      : "Invalid",
            "categories": "; ".join(tc["categories"]),
            "is_valid"  : tc["valid"]
        })

    # Add boundary cases that haven't already been included
    existing_dates = {row["date"] for row in all_cases}
    for tc in boundary_cases:
        if tc["date"] not in existing_dates:
            all_cases.append({
                "date"      : tc["date"],
                "type"      : "Boundary",
                "categories": "; ".join(tc["categories"]),
                "is_valid"  : tc["valid"]
            })

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["date", "type", "categories", "is_valid"])
        writer.writeheader()
        writer.writerows(all_cases)

    print(f"  [CSV] Saved → {filepath}")


def export_json(valid_cases, invalid_cases, boundary_cases, filepath):
    """Export best-evolved test cases to a structured JSON file."""
    output = {
        "valid_test_cases"   : [{"date": tc["date"],
                                  "categories": tc["categories"]}
                                 for tc in valid_cases],
        "invalid_test_cases" : [{"date": tc["date"],
                                  "categories": tc["categories"]}
                                 for tc in invalid_cases],
        "boundary_test_cases": [{"date": tc["date"],
                                  "categories": tc["categories"]}
                                 for tc in boundary_cases],
    }
    with open(filepath, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  [JSON] Saved → {filepath}")


def export_coverage_history(coverage_history, filepath):
    """
    Export generation-by-generation coverage percentages to CSV.
    Used to produce the line graph required in the report.
    """
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Generation", "Coverage_Pct"])
        for gen, cov in enumerate(coverage_history, start=1):
            writer.writerow([gen, cov])

    print(f"  [CSV] Coverage history saved → {filepath}")


# SECTION 14 — ENTRY POINT

if __name__ == "__main__":
    # Fix random seed for reproducibility
    random.seed(42)

    #  Print configuration 
    print("Running Genetic Algorithm for Date Test Case Generation...")
    print(f"Population Size   : {POPULATION_SIZE}")
    print(f"Max Generations   : {MAX_GENERATIONS}")
    print(f"Mutation Rate     : {MUTATION_RATE * 100:.0f}%")
    print(f"Coverage Goal     : {COVERAGE_GOAL}%")
    print(f"Target Categories : {TOTAL_CATEGORIES}")
    print("-" * 65)

    #  Run GA 
    final_pop, cov_history, gen_count, final_coverage = run_ga()

    #  Select best test cases from evolved population 
    valid_tc, invalid_tc, boundary_tc = select_best_test_cases(final_pop)

    #  Recompute coverage including all mandatory seed cases 
    all_chroms = [
        (int(tc["date"][:2]), int(tc["date"][3:5]), int(tc["date"][6:]))
        for tc in valid_tc + invalid_tc + boundary_tc
    ]
    covered_final, final_cov_pct = compute_coverage(all_chroms)

    #  Print output (assignment format) 
    print_output(valid_tc, invalid_tc, boundary_tc, final_cov_pct, gen_count)

    #  Export files 
    print("\nExporting test cases...")
    export_csv(valid_tc, invalid_tc, boundary_tc, "test_cases.csv")
    export_json(valid_tc, invalid_tc, boundary_tc, "test_cases.json")
    export_coverage_history(cov_history, "coverage_history.csv")

    print("\nDone. All files generated.")

    # RANDOM TESTING BASELINE
# Pure random generation — no fitness, selection, or crossover.
# Used to compare GA efficiency vs. random testing.



RANDOM_SAMPLE_SIZE = 100   # number of random samples to generate
 
def run_random_testing(num_samples=RANDOM_SAMPLE_SIZE):
    """
    Generate test cases one at a time using pure random sampling.
    Same chromosome ranges as GA: day[1-31], month[1-12], year[0-9999].
    Track cumulative coverage after every sample.
    Returns coverage history list and final coverage percentage.
    """
    random_pool    = []   # all generated chromosomes so far
    random_history = []   # coverage % recorded after each new sample
 
    print(f"\n  [Random] Running {num_samples} random samples for baseline...")
 
    for _ in range(num_samples):
        # Generate one random chromosome — same ranges as GA
        day   = random.randint(1, 31)
        month = random.randint(1, 12)
        year  = random.randint(0, 9999)
        random_pool.append((day, month, year))
 
        # Compute cumulative coverage after adding this sample
        _, cov_pct = compute_coverage(random_pool)
        random_history.append(round(cov_pct, 2))
 
    _, final_cov = compute_coverage(random_pool)
    cats_covered = int(final_cov * TOTAL_CATEGORIES / 100)
 
    print(f"  [Random] Final coverage: {final_cov:.2f}%  "
          f"({cats_covered}/{TOTAL_CATEGORIES} categories)")
 
    return random_history, final_cov
 
 
def export_comparison_csv(ga_history, random_history, filepath):
    """
    Export GA vs. Random Testing coverage side-by-side to CSV.
    GA coverage is held at its final value after it terminates.
    """
    num_rows = max(len(ga_history), len(random_history))
    ga_final = ga_history[-1]
 
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Sample_Number", "GA_Coverage_Pct", "Random_Coverage_Pct"])
        for i in range(num_rows):
            ga_cov   = ga_history[i]     if i < len(ga_history)     else ga_final
            rand_cov = random_history[i] if i < len(random_history) else random_history[-1]
            writer.writerow([i + 1, ga_cov, rand_cov])
 
    print(f"  [CSV] Comparison history saved → {filepath}")
 
 

# ENTRY POINT
 
if __name__ == "__main__":
    # Fix random seed for reproducibility
    random.seed(42)
 
    #  Print configuration 
    print("Running Genetic Algorithm for Date Test Case Generation...")
    print(f"Population Size   : {POPULATION_SIZE}")
    print(f"Max Generations   : {MAX_GENERATIONS}")
    print(f"Mutation Rate     : {MUTATION_RATE * 100:.0f}%")
    print(f"Coverage Goal     : {COVERAGE_GOAL}%")
    print(f"Target Categories : {TOTAL_CATEGORIES}")
    print("-" * 65)
 
    #  Run GA 
    final_pop, cov_history, gen_count, final_coverage = run_ga()
 
    #  Select best test cases from evolved population 
    valid_tc, invalid_tc, boundary_tc = select_best_test_cases(final_pop)
 
    #  Recompute coverage including all mandatory seed cases 
    all_chroms = [
        (int(tc["date"][:2]), int(tc["date"][3:5]), int(tc["date"][6:]))
        for tc in valid_tc + invalid_tc + boundary_tc
    ]
    covered_final, final_cov_pct = compute_coverage(all_chroms)
 
    #  Print output (assignment format) 
    print_output(valid_tc, invalid_tc, boundary_tc, final_cov_pct, gen_count)
 
    #  Run Random Testing baseline (continues from same RNG state as GA) 
    random_history, rand_final_cov = run_random_testing(RANDOM_SAMPLE_SIZE)
 
    #  Print comparison summary 
    print("\n" + "=" * 65)
    print("GA vs. Random Testing Summary:")
    print("=" * 65)
    print(f"  GA     — Coverage: {final_cov_pct:.0f}%   Generations: {gen_count}")
    print(f"  Random — Coverage: {rand_final_cov:.2f}%  Samples: {RANDOM_SAMPLE_SIZE}")
    print(f"  GA advantage: {final_cov_pct - rand_final_cov:.2f}% more coverage")
    print("=" * 65)
 
    #  Export files 
    print("\nExporting test cases...")
    export_csv(valid_tc, invalid_tc, boundary_tc, "test_cases.csv")
    export_json(valid_tc, invalid_tc, boundary_tc, "test_cases.json")
    export_coverage_history(cov_history, "coverage_history.csv")
    export_comparison_csv(cov_history, random_history, "comparison_history.csv")
 
    print("\nDone. All files generated.")