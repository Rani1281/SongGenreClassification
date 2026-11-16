import argparse


def subtract_files(large_file, exclude_file, output_file):
  with open(exclude_file, "r", encoding="utf-8") as f:
    exclude_set = {line.strip().lower() for line in f if line.strip()}

  with (
      open(large_file, "r", encoding="utf-8") as infile,
      open(output_file, "w", encoding="utf-8") as outfile,
  ):
    for line in infile:
      clean_path = line.strip()
      if clean_path and clean_path.lower() not in exclude_set:
        outfile.write(line)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      description="Subtract song paths in the second file from the first file."
  )
  parser.add_argument(
      "large_file", help="Path to the main/larger song list file"
  )
  parser.add_argument(
      "exclude_file", help="Path to the file containing songs to exclude"
  )
  parser.add_argument(
      "-o",
      "--output",
      default="filtered_songs.txt",
      help="Output file path (default: filtered_songs.txt)",
  )

  args = parser.parse_args()
  subtract_files(args.large_file, args.exclude_file, args.output)
  print(f"Done! Saved filtered list to: {args.output}")
