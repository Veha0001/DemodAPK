#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <nlohmann/json.hpp>
#include <optional>
#include <regex>
#include <sstream>
#include <string>
#include <vector>

// ANSI escape codes for colors
#define RESET "\033[0m"
#define RED "\033[31m"
#define GREEN "\033[32m"
#define YELLOW "\033[33m"
#define CYAN "\033[36m"

void replace_hex_at_offset(std::vector<uint8_t> &data, size_t offset,
                           const std::string &repl) {
  std::istringstream iss(repl);
  std::string byte_str;

  size_t idx = 0;
  while (iss >> byte_str) {
    if (idx + offset >= data.size()) {
      throw std::out_of_range("Replacement exceeds data size");
    }
    data[offset + idx] =
        static_cast<uint8_t>(std::stoul(byte_str, nullptr, 16));
    idx++;
  }
}

size_t wildcard_pattern_scan(const std::vector<uint8_t> &data,
                             const std::string &pattern) {
  std::istringstream iss(pattern);
  std::string byte_str;
  std::vector<int> pattern_bytes;

  while (iss >> byte_str) {
    pattern_bytes.push_back(
        byte_str == "??" ? -1
                         : static_cast<int>(std::stoul(byte_str, nullptr, 16)));
  }

  for (size_t i = 0; i <= data.size() - pattern_bytes.size(); ++i) {
    bool match = true;
    for (size_t j = 0; j < pattern_bytes.size(); ++j) {
      if (pattern_bytes[j] != -1 &&
          pattern_bytes[j] != static_cast<int>(data[i + j])) {
        match = false;
        break;
      }
    }
    if (match) {
      return i;
    }
  }
  return static_cast<size_t>(-1);
}

std::optional<size_t> find_offset_by_method_name(const std::string &method_name,
                                                 const std::string &dump_path) {
  std::ifstream dump_file(dump_path);
  if (!dump_file.is_open()) {
    std::cerr << RED << "Error: Dump file '" << dump_path << "' not found."
              << RESET << std::endl;
    return std::nullopt;
  }

  std::string line;
  std::regex offset_regex(R"(Offset:\s*0x([0-9A-Fa-f]+))");
  std::string previous_line;

  while (std::getline(dump_file, line)) {
    if (line.find(method_name) != std::string::npos) {
      // If we found the method, check the previous line for the offset
      if (!previous_line.empty()) {
        std::smatch match;
        if (std::regex_search(previous_line, match, offset_regex)) {
          size_t offset = std::stoul(match[1].str(), nullptr, 16);
          std::cout << GREEN << "Found " << method_name << " at Offset: 0x"
                    << std::hex << std::uppercase << offset << RESET
                    << std::endl;
          return offset;
        }
      }
      std::cout << YELLOW << "Warning: No offset found for " << method_name
                << "." << RESET << std::endl;
      return std::nullopt;
    }
    previous_line = line; // Store the current line to check it next time
  }
  return std::nullopt;
}

void patch_code(const std::string &input_filename,
                const std::string &output_filename,
                const nlohmann::json &patch_list,
                const std::string &dump_path) {
  std::ifstream input_file(input_filename, std::ios::binary);
  if (!input_file.is_open()) {
    std::cerr << RED << "Error: Input file '" << input_filename
              << "' not found." << RESET << std::endl;
    return;
  }

  std::vector<uint8_t> data((std::istreambuf_iterator<char>(input_file)),
                            std::istreambuf_iterator<char>());
  input_file.close();

  // Check if any patch uses a wildcard
  // for (const auto& patch : patch_list) {
  //    if (patch.contains("wildcard")) {
  //        std::cout << CYAN << "Note: Scanning with wildcards; this may take
  //        longer on larger files..." << RESET << std::endl; break;
  //    }
  //}

  for (const auto &patch : patch_list) {
    size_t offset = 0;

    if (patch.contains("method_name")) {
      auto result = find_offset_by_method_name(patch["method_name"], dump_path);
      if (!result) {
        std::cout << YELLOW << "Warning: Method '" << patch["method_name"]
                  << "' not found. Skipping patch." << RESET << std::endl;
        continue;
      }
      offset = *result;
    } else if (patch.contains("offset")) {
      offset = std::stoul(patch["offset"].get<std::string>(), nullptr,
                          16); // Convert hex string to integer
    } else if (patch.contains("wildcard")) {
      offset = wildcard_pattern_scan(data, patch["wildcard"]);
      if (offset == static_cast<size_t>(-1)) {
        std::cout << YELLOW << "Warning: No match found for wildcard pattern '"
                  << patch["wildcard"] << "'. Skipping patch." << RESET
                  << std::endl;
        continue;
      }
    } else {
      std::cout << YELLOW
                << "Warning: No valid patch definition found. Skipping."
                << RESET << std::endl;
      continue;
    }

    if (offset >= data.size()) {
      std::cout << RED << "Error: Offset 0x" << std::hex << std::uppercase
                << offset << " is out of range for the input file." << RESET
                << std::endl;
      continue;
    }

    std::cout << GREEN << "Patching at Offset: 0x" << std::hex << std::uppercase
              << offset << RESET << std::endl;
    replace_hex_at_offset(data, offset, patch["hex_code"]);
  }

  std::ofstream output_file(output_filename, std::ios::binary);
  if (!output_file.is_open()) {
    std::cerr << RED << "Error writing output file: " << output_filename
              << RESET << std::endl;
    return;
  }
  output_file.write(reinterpret_cast<const char *>(data.data()), data.size());
  output_file.close();

  std::cout << CYAN << "Patching completed. Output written to '"
            << output_filename << "'." << RESET << std::endl;
}

int main(int argc, char *argv[]) {
  std::string config_path = "config.json"; // Default configuration file name

  if (argc > 1) {
    config_path = argv[1]; // Use provided config path
  }

  nlohmann::json config;
  try {
    std::ifstream config_file(config_path);
    if (!config_file.is_open()) {
      std::cerr << RED << "Error: Configuration file '" << config_path
                << "' not found." << RESET << std::endl;
      return 1;
    }
    config_file >> config;
  } catch (const std::exception &e) {
    std::cerr << RED << "Error loading configuration: " << e.what() << RESET
              << std::endl;
    return 1;
  }

  // Extract necessary details
  std::string input_filename = config["Patcher"]["input_file"];
  std::string dump_path = config["Patcher"]["dump_file"];
  std::string output_filename = config["Patcher"]["output_file"];
  auto patch_list = config["Patcher"]["patches"];

  // Apply patches to binary
  patch_code(input_filename, output_filename, patch_list, dump_path);
  return 0;
}
